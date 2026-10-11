import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from assistencia_core import (
    ENCRYPTED_PREFIX,
    caminho_logo,
    configurar_seguranca,
    criptografar_senha,
    descriptografar_senha,
    estatisticas_por_status,
    migrar_logo,
    migrar_senhas,
    normalizar_status,
    recuperar_senha_mestra,
    status_inicial,
)


class AssistenciaCoreTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE aparelhos (id INTEGER PRIMARY KEY, status TEXT, senha TEXT, senha_versao INTEGER DEFAULT 0);
            CREATE TABLE seguranca_loja (
                id INTEGER PRIMARY KEY, versao INTEGER, master_salt BLOB, recovery_salt BLOB,
                pergunta_recuperacao TEXT, chave_mestra_protegida TEXT, chave_recuperacao_protegida TEXT
            );
        """)

    def tearDown(self):
        self.conn.close()

    def test_statuses_and_completed_counter(self):
        self.conn.executemany("INSERT INTO aparelhos(status) VALUES (?)", [
            ("pronto",), ("entregue",), ("em_manutencao",), ("concluido",),
        ])
        stats = estatisticas_por_status(self.conn)
        self.assertEqual(stats["recebidos"], 4)
        self.assertEqual(stats["concluidos"], 3)
        self.assertEqual(stats["por_status"]["pronto"], 2)
        self.assertEqual(normalizar_status("concluido"), "pronto")

    def test_initial_status_priority(self):
        self.assertEqual(status_inicial({"autorizado": True, "orcamento": True}), "aguardando_peca")
        self.assertEqual(status_inicial({"orcamento": True}), "em_orcamento")
        self.assertEqual(status_inicial({}), "aguardando_autorizacao")

    def test_encrypt_migrate_and_recover_master_password(self):
        self.conn.execute("INSERT INTO aparelhos(id, senha) VALUES (1, '1234')")
        key = configurar_seguranca(self.conn, "senha muito forte", "Cidade natal?", "Ponte Nova")
        self.assertEqual(migrar_senhas(self.conn, key), 1)
        saved = self.conn.execute("SELECT senha, senha_versao FROM aparelhos WHERE id=1").fetchone()
        self.assertTrue(saved["senha"].startswith(ENCRYPTED_PREFIX))
        self.assertEqual(saved["senha_versao"], 1)
        self.assertEqual(descriptografar_senha(saved["senha"], key), "1234")
        new_key = recuperar_senha_mestra(self.conn, "Ponte Nova", "outra senha forte")
        self.assertEqual(descriptografar_senha(saved["senha"], new_key), "1234")
        self.assertEqual(descriptografar_senha(criptografar_senha("abcd", new_key), new_key), "abcd")

    def test_portable_logo_path_and_missing_fallback(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            base = Path(directory)
            folder = base / "configuracoes"
            folder.mkdir()
            logo = folder / "marca.png"
            logo.write_bytes(b"not-an-image-but-a-file")
            self.assertEqual(migrar_logo(base, str(logo)), "configuracoes/marca.png")
            self.assertEqual(caminho_logo(base, "configuracoes/marca.png"), str(logo))
            self.assertEqual(caminho_logo(base, "C:/inexistente/marca.png"), "")


if __name__ == "__main__":
    unittest.main()
