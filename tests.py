import unittest
from app import create_app
from auth.auth_models import Usuario, PerfilUsuario
from tasks.task_models import Tarefa, Subtarefa, Comentario
from files.file_models import Arquivo
from lgpd import verificar_consentimento, anonimizar_dados
from datetime import datetime, timedelta
import os
import tempfile

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.db = self.app.extensions['sqlalchemy'].db
        self.db.create_all()
        
        # Criar perfil de teste
        perfil = PerfilUsuario(nome='cliente', descricao='Perfil de cliente')
        self.db.session.add(perfil)
        self.db.session.commit()
        
    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()
        
    def test_registro_usuario(self):
        # Testar registro de usuário
        response = self.client.post('/auth/registro', data={
            'nome': 'Teste',
            'sobrenome': 'Usuario',
            'email': 'teste@example.com',
            'senha': 'Senha123!',
            'confirmar_senha': 'Senha123!',
            'aceitar_termos': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        usuario = Usuario.query.filter_by(email='teste@example.com').first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nome, 'Teste')
        self.assertEqual(usuario.sobrenome, 'Usuario')
        
    def test_login_usuario(self):
        # Criar usuário para teste
        usuario = Usuario(
            nome='Teste',
            sobrenome='Login',
            email='login@example.com',
            perfil_id=1
        )
        usuario.set_password('Senha123!')
        self.db.session.add(usuario)
        self.db.session.commit()
        
        # Testar login
        response = self.client.post('/auth/login', data={
            'email': 'login@example.com',
            'senha': 'Senha123!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        
    def test_recuperacao_senha(self):
        # Criar usuário para teste
        usuario = Usuario(
            nome='Teste',
            sobrenome='Recuperacao',
            email='recuperacao@example.com',
            perfil_id=1
        )
        usuario.set_password('Senha123!')
        self.db.session.add(usuario)
        self.db.session.commit()
        
        # Testar solicitação de recuperação
        response = self.client.post('/auth/recuperar-senha', data={
            'email': 'recuperacao@example.com'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email de recupera', response.data)  # Mensagem de confirmação

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.db = self.app.extensions['sqlalchemy'].db
        self.db.create_all()
        
        # Criar perfil e usuário de teste
        perfil = PerfilUsuario(nome='cliente', descricao='Perfil de cliente')
        self.db.session.add(perfil)
        
        usuario = Usuario(
            nome='Teste',
            sobrenome='Tarefas',
            email='tarefas@example.com',
            perfil_id=1
        )
        usuario.set_password('Senha123!')
        self.db.session.add(usuario)
        self.db.session.commit()
        
        # Login do usuário
        self.client.post('/auth/login', data={
            'email': 'tarefas@example.com',
            'senha': 'Senha123!'
        })
        
    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()
        
    def test_criar_tarefa(self):
        # Testar criação de tarefa
        response = self.client.post('/tasks/', data={
            'titulo': 'Tarefa de Teste',
            'descricao': 'Descrição da tarefa de teste',
            'classificacao': 'importancia',
            'prioridade': 'media',
            'data_prazo': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        tarefa = Tarefa.query.filter_by(titulo='Tarefa de Teste').first()
        self.assertIsNotNone(tarefa)
        self.assertEqual(tarefa.descricao, 'Descrição da tarefa de teste')
        self.assertEqual(tarefa.classificacao.value, 'importancia')
        
    def test_adicionar_subtarefa(self):
        # Criar tarefa para teste
        tarefa = Tarefa(
            titulo='Tarefa Principal',
            descricao='Tarefa para testar subtarefas',
            classificacao='importancia',
            usuario_id=1
        )
        self.db.session.add(tarefa)
        self.db.session.commit()
        
        # Testar adição de subtarefa
        response = self.client.post(f'/tasks/{tarefa.id}/subtarefas', data={
            'titulo': 'Subtarefa de Teste'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        subtarefa = Subtarefa.query.filter_by(titulo='Subtarefa de Teste').first()
        self.assertIsNotNone(subtarefa)
        self.assertEqual(subtarefa.tarefa_id, tarefa.id)
        
    def test_adicionar_comentario(self):
        # Criar tarefa para teste
        tarefa = Tarefa(
            titulo='Tarefa com Comentário',
            descricao='Tarefa para testar comentários',
            classificacao='rotina',
            usuario_id=1
        )
        self.db.session.add(tarefa)
        self.db.session.commit()
        
        # Testar adição de comentário
        response = self.client.post(f'/tasks/{tarefa.id}/comentarios', data={
            'conteudo': 'Este é um comentário de teste'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        comentario = Comentario.query.filter_by(tarefa_id=tarefa.id).first()
        self.assertIsNotNone(comentario)
        self.assertEqual(comentario.conteudo, 'Este é um comentário de teste')

class TestFiles(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.db = self.app.extensions['sqlalchemy'].db
        self.db.create_all()
        
        # Criar diretório temporário para uploads
        self.test_upload_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.test_upload_dir
        
        # Criar perfil e usuário de teste
        perfil = PerfilUsuario(nome='cliente', descricao='Perfil de cliente')
        self.db.session.add(perfil)
        
        usuario = Usuario(
            nome='Teste',
            sobrenome='Arquivos',
            email='arquivos@example.com',
            perfil_id=1
        )
        usuario.set_password('Senha123!')
        self.db.session.add(usuario)
        self.db.session.commit()
        
        # Login do usuário
        self.client.post('/auth/login', data={
            'email': 'arquivos@example.com',
            'senha': 'Senha123!'
        })
        
    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()
        
        # Limpar diretório de uploads
        for filename in os.listdir(self.test_upload_dir):
            os.unlink(os.path.join(self.test_upload_dir, filename))
        os.rmdir(self.test_upload_dir)
        
    def test_upload_arquivo(self):
        # Criar arquivo de teste
        test_file_content = b'Conteudo de teste do arquivo'
        test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        test_file.write(test_file_content)
        test_file.close()
        
        # Testar upload de arquivo
        with open(test_file.name, 'rb') as f:
            response = self.client.post('/files/', data={
                'arquivo': (f, 'teste.txt'),
                'descricao': 'Arquivo de teste'
            }, follow_redirects=True, content_type='multipart/form-data')
            
        self.assertEqual(response.status_code, 200)
        arquivo = Arquivo.query.filter_by(nome='teste.txt').first()
        self.assertIsNotNone(arquivo)
        self.assertEqual(arquivo.tipo, 'text/plain')
        self.assertEqual(arquivo.descricao, 'Arquivo de teste')
        
        # Limpar arquivo temporário
        os.unlink(test_file.name)
        
    def test_download_arquivo(self):
        # Criar arquivo para teste
        arquivo = Arquivo(
            nome='download_teste.txt',
            tipo='text/plain',
            tamanho=20,
            caminho=os.path.join(self.test_upload_dir, 'download_teste.txt'),
            descricao='Arquivo para testar download',
            usuario_id=1
        )
        self.db.session.add(arquivo)
        self.db.session.commit()
        
        # Criar arquivo físico
        with open(os.path.join(self.test_upload_dir, 'download_teste.txt'), 'w') as f:
            f.write('Conteúdo para download')
        
        # Testar download
        response = self.client.get(f'/files/{arquivo.id}/download')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename=download_teste.txt')

class TestLGPD(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.db = self.app.extensions['sqlalchemy'].db
        self.db.create_all()
        
        # Criar perfil e usuário de teste
        perfil = PerfilUsuario(nome='cliente', descricao='Perfil de cliente')
        self.db.session.add(perfil)
        
        usuario = Usuario(
            nome='Teste',
            sobrenome='LGPD',
            email='lgpd@example.com',
            perfil_id=1
        )
        usuario.set_password('Senha123!')
        self.db.session.add(usuario)
        self.db.session.commit()
        
        # Login do usuário
        self.client.post('/auth/login', data={
            'email': 'lgpd@example.com',
            'senha': 'Senha123!'
        })
        
    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()
        
    def test_gerenciar_consentimentos(self):
        # Testar atualização de consentimentos
        response = self.client.post('/lgpd/consent', data={
            'dados_pessoais': 'on',
            'comunicacoes': 'on',
            'cookies': 'on'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(verificar_consentimento(1, 'dados_pessoais'))
        self.assertTrue(verificar_consentimento(1, 'comunicacoes'))
        self.assertTrue(verificar_consentimento(1, 'cookies'))
        self.assertFalse(verificar_consentimento(1, 'compartilhamento'))
        
    def test_anonimizacao_dados(self):
        # Testar anonimização de dados
        usuario_id = 1
        resultado = anonimizar_dados(usuario_id)
        
        self.assertTrue(resultado)
        usuario = Usuario.query.get(usuario_id)
        self.assertEqual(usuario.nome, 'Usuário Anonimizado')
        self.assertTrue(usuario.anonimizado)
        self.assertIsNotNone(usuario.data_anonimizacao)

if __name__ == '__main__':
    unittest.main()
