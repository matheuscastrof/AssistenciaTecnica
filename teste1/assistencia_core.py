"""Regras compartilhadas de status, senhas protegidas e arquivos da loja."""

import base64
import hashlib
import os
import shutil
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


STATUS_INFO = {
    "em_orcamento": ("#2583E8", "Em Orçamento", "Orçamento em elaboração", "REQUEST_QUOTE_ROUNDED"),
    "aguardando_autorizacao": ("#6738E8", "Aguardando Autorização", "Aguardando resposta do cliente", "SHIELD_ROUNDED"),
    "aguardando_peca": ("#F39A16", "Aguardando Peça", "Aguardando chegada de peça", "INVENTORY_2_ROUNDED"),
    "em_manutencao": ("#F5A623", "Em Manutenção", "Reparo em andamento", "BUILD_ROUNDED"),
    "pronto": ("#17B96B", "Aparelho Pronto", "Pronto para retirada", "PHONE_ANDROID_ROUNDED"),
    "entregue": ("#7A5AF8", "Aparelho Entregue", "Entregue ao cliente", "LOCAL_SHIPPING_ROUNDED"),
    "sem_solucao": ("#E51D25", "Sem Solução", "Sem solução no momento", "BUILD_ROUNDED"),
}
STATUS_ORDER = tuple(STATUS_INFO)
LEGACY_STATUS = {"concluido": "pronto"}
CONCLUDED_STATUSES = ("pronto", "entregue")
ENCRYPTED_PREFIX = "enc:v1:"


def normalizar_status(status):
    status = (status or "aguardando_autorizacao").strip()
    return LEGACY_STATUS.get(status, status if status in STATUS_INFO else "aguardando_autorizacao")


def status_inicial(dados):
    """Regra operacional escolhida para novas OS."""
    if dados.get("autorizado"):
        return "aguardando_peca"
    if dados.get("orcamento"):
        return "em_orcamento"
    return "aguardando_autorizacao"


def estatisticas_por_status(conn):
    contagens = {status: 0 for status in STATUS_ORDER}
    for row in conn.execute("SELECT status, COUNT(*) AS total FROM aparelhos GROUP BY status"):
        contagens[normalizar_status(row["status"])] += int(row["total"])
    total = sum(contagens.values())
    return {
        "por_status": contagens,
        "recebidos": total,
        "em_manutencao": contagens["em_manutencao"],
        "concluidos": sum(contagens[status] for status in CONCLUDED_STATUSES),
    }


def _derive_fernet_key(secret, salt):
    material = hashlib.pbkdf2_hmac(
        "sha256", (secret or "").encode("utf-8"), salt, 600_000, dklen=32
    )
    return base64.urlsafe_b64encode(material)


def _encrypt_for_secret(data_key, secret, salt):
    return Fernet(_derive_fernet_key(secret, salt)).encrypt(data_key).decode("ascii")


def _decrypt_for_secret(token, secret, salt):
    return Fernet(_derive_fernet_key(secret, salt)).decrypt(token.encode("ascii"))


def obter_seguranca(conn):
    row = conn.execute("SELECT * FROM seguranca_loja WHERE id = 1").fetchone()
    return dict(row) if row else None


def configurar_seguranca(conn, senha_mestra, pergunta_recuperacao, resposta_recuperacao):
    if len(senha_mestra or "") < 8:
        raise ValueError("A senha-mestra deve ter ao menos 8 caracteres.")
    if not (pergunta_recuperacao or "").strip() or not (resposta_recuperacao or "").strip():
        raise ValueError("Informe a pergunta e a resposta de recuperação.")
    data_key = Fernet.generate_key()
    master_salt, recovery_salt = os.urandom(16), os.urandom(16)
    conn.execute(
        """INSERT INTO seguranca_loja
           (id, versao, master_salt, recovery_salt, pergunta_recuperacao,
            chave_mestra_protegida, chave_recuperacao_protegida)
           VALUES (1, 1, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET versao=1, master_salt=excluded.master_salt,
             recovery_salt=excluded.recovery_salt, pergunta_recuperacao=excluded.pergunta_recuperacao,
             chave_mestra_protegida=excluded.chave_mestra_protegida,
             chave_recuperacao_protegida=excluded.chave_recuperacao_protegida""",
        (
            master_salt, recovery_salt, pergunta_recuperacao.strip(),
            _encrypt_for_secret(data_key, senha_mestra, master_salt),
            _encrypt_for_secret(data_key, resposta_recuperacao, recovery_salt),
        ),
    )
    return data_key


def desbloquear_com_senha(conn, senha_mestra):
    config = obter_seguranca(conn)
    if not config:
        raise ValueError("A senha-mestra ainda não foi configurada.")
    try:
        return _decrypt_for_secret(config["chave_mestra_protegida"], senha_mestra, config["master_salt"])
    except InvalidToken as erro:
        raise ValueError("Senha-mestra incorreta.") from erro


def recuperar_senha_mestra(conn, resposta_recuperacao, nova_senha_mestra):
    if len(nova_senha_mestra or "") < 8:
        raise ValueError("A nova senha-mestra deve ter ao menos 8 caracteres.")
    config = obter_seguranca(conn)
    if not config:
        raise ValueError("A senha-mestra ainda não foi configurada.")
    try:
        data_key = _decrypt_for_secret(
            config["chave_recuperacao_protegida"], resposta_recuperacao, config["recovery_salt"]
        )
    except InvalidToken as erro:
        raise ValueError("Resposta de recuperação incorreta.") from erro
    salt = os.urandom(16)
    conn.execute(
        "UPDATE seguranca_loja SET master_salt=?, chave_mestra_protegida=? WHERE id=1",
        (salt, _encrypt_for_secret(data_key, nova_senha_mestra, salt)),
    )
    return data_key


def criptografar_senha(valor, data_key):
    if not valor:
        return ""
    if str(valor).startswith(ENCRYPTED_PREFIX):
        return valor
    return ENCRYPTED_PREFIX + Fernet(data_key).encrypt(str(valor).encode("utf-8")).decode("ascii")


def descriptografar_senha(valor, data_key):
    if not valor:
        return ""
    if not str(valor).startswith(ENCRYPTED_PREFIX):
        return str(valor)
    if not data_key:
        raise ValueError("Desbloqueie a senha-mestra para acessar a senha do aparelho.")
    try:
        return Fernet(data_key).decrypt(str(valor)[len(ENCRYPTED_PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken as erro:
        raise ValueError("Não foi possível ler a senha protegida do aparelho.") from erro


def migrar_senhas(conn, data_key):
    """Cifra registros legados em texto aberto na mesma transação do chamador."""
    rows = conn.execute(
        "SELECT id, senha FROM aparelhos WHERE senha IS NOT NULL AND senha != '' AND senha_versao = 0"
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE aparelhos SET senha=?, senha_versao=1 WHERE id=?",
            (criptografar_senha(row["senha"], data_key), row["id"]),
        )
    return len(rows)


def caminho_logo(base_dir, valor):
    """Resolve apenas logos pertencentes à pasta configuracoes do projeto."""
    if not valor:
        return ""
    base = Path(base_dir).resolve()
    candidate = (base / valor).resolve() if not os.path.isabs(valor) else Path(valor).resolve()
    config_dir = (base / "configuracoes").resolve()
    try:
        candidate.relative_to(config_dir)
    except ValueError:
        return ""
    return str(candidate) if candidate.is_file() else ""


def migrar_logo(base_dir, valor):
    """Retorna caminho relativo seguro e, quando possível, importa logo antiga."""
    if not valor:
        return ""
    base = Path(base_dir).resolve()
    config_dir = base / "configuracoes"
    config_dir.mkdir(exist_ok=True)
    current = caminho_logo(base, valor)
    if current:
        return str(Path(current).relative_to(base)).replace("\\", "/")
    legacy = Path(valor)
    local_same_name = config_dir / legacy.name
    if local_same_name.is_file():
        return str(local_same_name.relative_to(base)).replace("\\", "/")
    if legacy.is_file():
        destination = config_dir / f"logo_loja_migrada_{legacy.name}"
        shutil.copy2(legacy, destination)
        return str(destination.relative_to(base)).replace("\\", "/")
    return ""


def salvar_logo(base_dir, origem):
    base = Path(base_dir).resolve()
    config_dir = base / "configuracoes"
    config_dir.mkdir(exist_ok=True)
    source = Path(origem)
    if not source.is_file():
        raise FileNotFoundError("Não foi possível acessar a imagem selecionada.")
    destination = config_dir / f"logo_loja_{os.urandom(8).hex()}{source.suffix.lower() or '.png'}"
    shutil.copy2(source, destination)
    return str(destination.relative_to(base)).replace("\\", "/")


def remover_logo_gerenciada(base_dir, valor):
    path = caminho_logo(base_dir, valor)
    if path:
        Path(path).unlink(missing_ok=True)
