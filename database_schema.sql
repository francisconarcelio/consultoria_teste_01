-- Esquema do Banco de Dados para o Sistema de Consultoria Educacional
-- Serra Projetos Educacionais

-- Configurações iniciais
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

-- -----------------------------------------------------
-- Tabela `usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome_completo` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `username` VARCHAR(50) NOT NULL,
  `senha_hash` VARCHAR(255) NOT NULL,
  `salt` VARCHAR(100) NOT NULL,
  `tipo` ENUM('admin', 'consultor', 'gestor', 'cliente') NOT NULL DEFAULT 'cliente',
  `status` ENUM('ativo', 'inativo', 'bloqueado', 'pendente') NOT NULL DEFAULT 'pendente',
  `ultimo_login` DATETIME NULL,
  `tentativas_login` INT NOT NULL DEFAULT 0,
  `token_recuperacao` VARCHAR(100) NULL,
  `expiracao_token` DATETIME NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `perfis_usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `perfis_usuarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `telefone` VARCHAR(20) NULL,
  `foto_perfil` VARCHAR(255) NULL,
  `cargo` VARCHAR(100) NULL,
  `departamento` VARCHAR(100) NULL,
  `bio` TEXT NULL,
  `preferencias` JSON NULL,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_perfis_usuarios_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_perfis_usuarios_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `autenticacao_externa`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autenticacao_externa` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `provedor` ENUM('google', 'apple', 'microsoft') NOT NULL,
  `provedor_id` VARCHAR(255) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `token` TEXT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `provedor_provedor_id_UNIQUE` (`provedor`, `provedor_id` ASC),
  INDEX `fk_autenticacao_externa_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_autenticacao_externa_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `logs_autenticacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `logs_autenticacao` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NULL,
  `email` VARCHAR(100) NULL,
  `ip` VARCHAR(45) NOT NULL,
  `user_agent` TEXT NOT NULL,
  `acao` ENUM('login_sucesso', 'login_falha', 'logout', 'recuperacao_senha', 'alteracao_senha', 'bloqueio') NOT NULL,
  `detalhes` TEXT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_logs_autenticacao_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_logs_autenticacao_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `instituicoes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `instituicoes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(100) NOT NULL,
  `tipo` ENUM('escola', 'universidade', 'curso', 'outro') NOT NULL,
  `segmento` VARCHAR(100) NULL,
  `num_alunos` INT NULL,
  `num_professores` INT NULL,
  `localizacao` VARCHAR(100) NULL,
  `endereco` VARCHAR(255) NULL,
  `cidade` VARCHAR(100) NULL,
  `estado` VARCHAR(50) NULL,
  `cep` VARCHAR(20) NULL,
  `telefone` VARCHAR(20) NULL,
  `email` VARCHAR(100) NULL,
  `website` VARCHAR(255) NULL,
  `data_cadastro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `usuarios_instituicoes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios_instituicoes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `instituicao_id` INT NOT NULL,
  `cargo` VARCHAR(100) NULL,
  `permissoes` JSON NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `usuario_instituicao_UNIQUE` (`usuario_id`, `instituicao_id` ASC),
  INDEX `fk_usuarios_instituicoes_usuarios_idx` (`usuario_id` ASC),
  INDEX `fk_usuarios_instituicoes_instituicoes_idx` (`instituicao_id` ASC),
  CONSTRAINT `fk_usuarios_instituicoes_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_usuarios_instituicoes_instituicoes`
    FOREIGN KEY (`instituicao_id`)
    REFERENCES `instituicoes` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `arquivos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `arquivos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `tipo` VARCHAR(50) NOT NULL,
  `extensao` VARCHAR(10) NOT NULL,
  `tamanho` INT NOT NULL,
  `caminho` VARCHAR(255) NOT NULL,
  `hash_conteudo` VARCHAR(64) NULL,
  `conteudo_texto` LONGTEXT NULL,
  `metadados` JSON NULL,
  `usuario_id` INT NOT NULL,
  `instituicao_id` INT NULL,
  `publico` TINYINT(1) NOT NULL DEFAULT 0,
  `data_upload` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_arquivos_usuarios_idx` (`usuario_id` ASC),
  INDEX `fk_arquivos_instituicoes_idx` (`instituicao_id` ASC),
  CONSTRAINT `fk_arquivos_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_arquivos_instituicoes`
    FOREIGN KEY (`instituicao_id`)
    REFERENCES `instituicoes` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `categorias_tarefas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `categorias_tarefas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(50) NOT NULL,
  `descricao` TEXT NULL,
  `cor` VARCHAR(7) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `nome_UNIQUE` (`nome` ASC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir categorias padrão
INSERT INTO `categorias_tarefas` (`nome`, `descricao`, `cor`) VALUES
('IMPORTÂNCIA', 'Tarefas importantes que contribuem para objetivos de longo prazo', '#FF5733'),
('ROTINA', 'Tarefas recorrentes que fazem parte do dia a dia', '#33A1FF'),
('URGÊNCIA', 'Tarefas que requerem atenção imediata', '#FF3333'),
('PAUSA', 'Tarefas em espera ou pausadas temporariamente', '#AAAAAA');

-- -----------------------------------------------------
-- Tabela `tarefas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tarefas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(100) NOT NULL,
  `descricao` TEXT NULL,
  `categoria_id` INT NOT NULL,
  `usuario_id` INT NOT NULL,
  `instituicao_id` INT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_vencimento` DATETIME NULL,
  `data_conclusao` DATETIME NULL,
  `prioridade` ENUM('baixa', 'media', 'alta', 'critica') NOT NULL DEFAULT 'media',
  `status` ENUM('pendente', 'em_andamento', 'concluida', 'cancelada', 'pausada') NOT NULL DEFAULT 'pendente',
  `recorrente` TINYINT(1) NOT NULL DEFAULT 0,
  `padrao_recorrencia` VARCHAR(50) NULL,
  `notificacoes` TINYINT(1) NOT NULL DEFAULT 1,
  `evento_calendario_id` VARCHAR(255) NULL,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_tarefas_categorias_tarefas_idx` (`categoria_id` ASC),
  INDEX `fk_tarefas_usuarios_idx` (`usuario_id` ASC),
  INDEX `fk_tarefas_instituicoes_idx` (`instituicao_id` ASC),
  CONSTRAINT `fk_tarefas_categorias_tarefas`
    FOREIGN KEY (`categoria_id`)
    REFERENCES `categorias_tarefas` (`id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_tarefas_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_tarefas_instituicoes`
    FOREIGN KEY (`instituicao_id`)
    REFERENCES `instituicoes` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `arquivos_tarefas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `arquivos_tarefas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `tarefa_id` INT NOT NULL,
  `arquivo_id` INT NOT NULL,
  `data_associacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `tarefa_arquivo_UNIQUE` (`tarefa_id`, `arquivo_id` ASC),
  INDEX `fk_arquivos_tarefas_tarefas_idx` (`tarefa_id` ASC),
  INDEX `fk_arquivos_tarefas_arquivos_idx` (`arquivo_id` ASC),
  CONSTRAINT `fk_arquivos_tarefas_tarefas`
    FOREIGN KEY (`tarefa_id`)
    REFERENCES `tarefas` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_arquivos_tarefas_arquivos`
    FOREIGN KEY (`arquivo_id`)
    REFERENCES `arquivos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `comentarios_tarefas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `comentarios_tarefas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `tarefa_id` INT NOT NULL,
  `usuario_id` INT NOT NULL,
  `comentario` TEXT NOT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_comentarios_tarefas_tarefas_idx` (`tarefa_id` ASC),
  INDEX `fk_comentarios_tarefas_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_comentarios_tarefas_tarefas`
    FOREIGN KEY (`tarefa_id`)
    REFERENCES `tarefas` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_comentarios_tarefas_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `integracao_google_calendar`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `integracao_google_calendar` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `token_acesso` TEXT NOT NULL,
  `token_atualizacao` TEXT NOT NULL,
  `expiracao_token` DATETIME NOT NULL,
  `calendario_id` VARCHAR(255) NULL,
  `sincronizacao_ativa` TINYINT(1) NOT NULL DEFAULT 1,
  `ultima_sincronizacao` DATETIME NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `usuario_id_UNIQUE` (`usuario_id` ASC),
  CONSTRAINT `fk_integracao_google_calendar_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `diagnosticos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `diagnosticos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `instituicao_id` INT NOT NULL,
  `usuario_id` INT NOT NULL,
  `titulo` VARCHAR(100) NOT NULL,
  `pilares` JSON NOT NULL,
  `resultados` JSON NOT NULL,
  `recomendacoes` JSON NOT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_diagnosticos_instituicoes_idx` (`instituicao_id` ASC),
  INDEX `fk_diagnosticos_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_diagnosticos_instituicoes`
    FOREIGN KEY (`instituicao_id`)
    REFERENCES `instituicoes` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_diagnosticos_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `simulacoes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `simulacoes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `instituicao_id` INT NOT NULL,
  `usuario_id` INT NOT NULL,
  `titulo` VARCHAR(100) NOT NULL,
  `cenario` VARCHAR(50) NOT NULL,
  `parametros` JSON NOT NULL,
  `horizonte_temporal` INT NOT NULL,
  `resultados` JSON NOT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_simulacoes_instituicoes_idx` (`instituicao_id` ASC),
  INDEX `fk_simulacoes_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_simulacoes_instituicoes`
    FOREIGN KEY (`instituicao_id`)
    REFERENCES `instituicoes` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_simulacoes_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `logs_sistema`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `logs_sistema` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NULL,
  `tipo` ENUM('info', 'warning', 'error', 'security', 'audit') NOT NULL,
  `acao` VARCHAR(100) NOT NULL,
  `descricao` TEXT NOT NULL,
  `ip` VARCHAR(45) NULL,
  `user_agent` TEXT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_logs_sistema_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_logs_sistema_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `consentimentos_lgpd`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `consentimentos_lgpd` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `tipo_consentimento` VARCHAR(100) NOT NULL,
  `texto_consentimento` TEXT NOT NULL,
  `versao` VARCHAR(20) NOT NULL,
  `consentimento_dado` TINYINT(1) NOT NULL DEFAULT 0,
  `data_consentimento` DATETIME NULL,
  `ip` VARCHAR(45) NULL,
  `user_agent` TEXT NULL,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_consentimentos_lgpd_usuarios_idx` (`usuario_id` ASC),
  CONSTRAINT `fk_consentimentos_lgpd_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Tabela `configuracoes_sistema`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `configuracoes_sistema` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `chave` VARCHAR(100) NOT NULL,
  `valor` TEXT NOT NULL,
  `descricao` TEXT NULL,
  `tipo` VARCHAR(50) NOT NULL DEFAULT 'string',
  `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `chave_UNIQUE` (`chave` ASC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir configurações iniciais
INSERT INTO `configuracoes_sistema` (`chave`, `valor`, `descricao`, `tipo`) VALUES
('max_file_size', '10485760', 'Tamanho máximo de arquivo em bytes (10MB)', 'integer'),
('allowed_file_types', 'pdf,doc,docx,txt', 'Tipos de arquivos permitidos para upload', 'string'),
('max_login_attempts', '5', 'Número máximo de tentativas de login antes do bloqueio', 'integer'),
('password_expiry_days', '90', 'Dias até a expiração da senha', 'integer'),
('session_timeout_minutes', '30', 'Tempo de inatividade até expiração da sessão', 'integer'),
('enable_google_calendar', 'true', 'Habilitar integração com Google Calendar', 'boolean'),
('enable_external_auth', 'true', 'Habilitar autenticação externa (Google, Apple, Microsoft)', 'boolean'),
('terms_version', '1.0', 'Versão atual dos termos de uso', 'string'),
('privacy_policy_version', '1.0', 'Versão atual da política de privacidade', 'string');
