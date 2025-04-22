// JavaScript para o Agente de IA para Consultoria Educacional

document.addEventListener('DOMContentLoaded', function() {
    // Inicialização de gráficos
    initCharts();
    
    // Configuração de navegação
    setupNavigation();
    
    // Configuração de formulários
    setupForms();
    
    // Configuração do chat
    setupChat();
    
    // Configuração do slider de horizonte temporal
    setupHorizonteSlider();
    
    // Configuração de segurança
    setupSecurity();
});

// Inicialização de gráficos
function initCharts() {
    // Gráfico de distribuição por pilar
    const pillarCtx = document.getElementById('pillarChart').getContext('2d');
    const pillarChart = new Chart(pillarCtx, {
        type: 'doughnut',
        data: {
            labels: ['Pedagógico', 'Comercial', 'Marketing', 'Financeiro'],
            datasets: [{
                data: [35, 25, 20, 20],
                backgroundColor: [
                    '#0d6efd',
                    '#20c997',
                    '#fd7e14',
                    '#6f42c1'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Configuração de navegação
function setupNavigation() {
    // Obter todos os links de navegação
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const sections = document.querySelectorAll('.section-content');
    
    // Adicionar evento de clique a cada link
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remover classe active de todos os links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Adicionar classe active ao link clicado
            this.classList.add('active');
            
            // Obter o ID da seção a ser mostrada
            const targetId = this.id.replace('-link', '-section');
            
            // Esconder todas as seções
            sections.forEach(section => section.classList.add('d-none'));
            
            // Mostrar a seção alvo
            document.getElementById(targetId).classList.remove('d-none');
        });
    });
}

// Configuração de formulários
function setupForms() {
    // Formulário de diagnóstico
    const diagnosticoForm = document.getElementById('diagnostico-form');
    if (diagnosticoForm) {
        diagnosticoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Obter valores do formulário
            const instituicaoId = document.getElementById('instituicao-select').value;
            const pilarPedagogico = document.getElementById('pilar-pedagogico').checked;
            const pilarComercial = document.getElementById('pilar-comercial').checked;
            const pilarMarketing = document.getElementById('pilar-marketing').checked;
            const pilarFinanceiro = document.getElementById('pilar-financeiro').checked;
            const contexto = document.getElementById('contexto-textarea').value;
            
            // Verificar se pelo menos um pilar foi selecionado
            if (!pilarPedagogico && !pilarComercial && !pilarMarketing && !pilarFinanceiro) {
                alert('Selecione pelo menos um pilar para análise.');
                return;
            }
            
            // Simular chamada à API
            simulateDiagnosticoAPI(instituicaoId, {
                pedagogico: pilarPedagogico,
                comercial: pilarComercial,
                marketing: pilarMarketing,
                financeiro: pilarFinanceiro
            }, contexto);
        });
    }
    
    // Formulário de simulação
    const simulacaoForm = document.getElementById('simulacao-form');
    if (simulacaoForm) {
        simulacaoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Obter valores do formulário
            const instituicaoId = document.getElementById('sim-instituicao-select').value;
            const cenario = document.getElementById('cenario-select').value;
            const horizonte = document.getElementById('horizonte-range').value;
            const parametros = document.getElementById('parametros-textarea').value;
            
            // Simular chamada à API
            simulateSimulacaoAPI(instituicaoId, cenario, horizonte, parametros);
        });
    }
    
    // Formulário de nova instituição
    const salvarInstituicaoBtn = document.getElementById('salvar-instituicao');
    if (salvarInstituicaoBtn) {
        salvarInstituicaoBtn.addEventListener('click', function() {
            const form = document.getElementById('nova-instituicao-form');
            
            // Verificar se o formulário é válido
            if (!form.checkValidity()) {
                // Trigger validation
                const event = new Event('submit', {
                    'bubbles': true,
                    'cancelable': true
                });
                form.dispatchEvent(event);
                return;
            }
            
            // Obter valores do formulário
            const nome = document.getElementById('inst-nome').value;
            const tipo = document.getElementById('inst-tipo').value;
            const segmento = document.getElementById('inst-segmento').value;
            const localizacao = document.getElementById('inst-localizacao').value;
            const alunos = document.getElementById('inst-alunos').value;
            const professores = document.getElementById('inst-professores').value;
            const observacoes = document.getElementById('inst-observacoes').value;
            
            // Simular salvamento
            alert(`Instituição "${nome}" cadastrada com sucesso!`);
            
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('novaInstituicaoModal'));
            modal.hide();
            
            // Limpar formulário
            form.reset();
        });
    }
}

// Configuração do chat
function setupChat() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');
    
    if (chatInput && sendButton && chatMessages) {
        // Função para adicionar mensagem ao chat
        function addMessage(message, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${isUser ? 'user-message' : 'system-message'}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Processar quebras de linha
            const paragraphs = message.split('\n').filter(p => p.trim() !== '');
            paragraphs.forEach(paragraph => {
                const p = document.createElement('p');
                p.textContent = paragraph;
                contentDiv.appendChild(p);
            });
            
            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            
            // Rolar para o final
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Evento de envio de mensagem
        function sendMessage() {
            const message = chatInput.value.trim();
            if (message) {
                // Adicionar mensagem do usuário
                addMessage(message, true);
                
                // Limpar input
                chatInput.value = '';
                
                // Simular resposta do assistente (com delay para parecer mais natural)
                setTimeout(() => {
                    simulateChatAPI(message);
                }, 500);
            }
        }
        
        // Adicionar evento de clique ao botão de envio
        sendButton.addEventListener('click', sendMessage);
        
        // Adicionar evento de tecla Enter ao input
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

// Configuração do slider de horizonte temporal
function setupHorizonteSlider() {
    const horizonteRange = document.getElementById('horizonte-range');
    const horizonteValue = document.getElementById('horizonte-value');
    
    if (horizonteRange && horizonteValue) {
        horizonteRange.addEventListener('input', function() {
            horizonteValue.textContent = this.value;
        });
    }
}

// Simulação de chamada à API de diagnóstico
function simulateDiagnosticoAPI(instituicaoId, pilares, contexto) {
    // Mostrar indicador de carregamento
    const resultadosDiv = document.getElementById('diagnostico-resultados');
    resultadosDiv.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div><p class="mt-3">Realizando diagnóstico...</p></div>';
    
    // Simular delay de processamento
    setTimeout(() => {
        // Dados simulados para cada pilar
        const resultados = {
            pedagogico: {
                coerencia_ppp: Math.random() * 0.3 + 0.6,
                integracao_curricular: Math.random() * 0.3 + 0.5,
                desenvolvimento_profissional: Math.random() * 0.3 + 0.6,
                praticas_avaliativas: Math.random() * 0.3 + 0.5
            },
            comercial: {
                taxa_conversao: Math.random() * 0.2 + 0.1,
                taxa_renovacao: Math.random() * 0.2 + 0.7,
                satisfacao_clientes: Math.random() * 0.2 + 0.7
            },
            marketing: {
                engajamento_redes: Math.random() * 0.4 + 0.3,
                percepcao_marca: Math.random() * 0.3 + 0.6,
                eficacia_campanhas: Math.random() * 0.3 + 0.4
            },
            financeiro: {
                sustentabilidade: Math.random() * 0.3 + 0.6,
                eficiencia_operacional: Math.random() * 0.3 + 0.6,
                investimento_formacao: Math.random() * 0.4 + 0.3
            }
        };
        
        // Recomendações simuladas para cada pilar
        const recomendacoes = {
            pedagogico: [
                "Implementar rodas de conversa semanais para fortalecer a integração curricular",
                "Desenvolver um programa de formação continuada baseado nas narrativas docentes",
                "Revisar as práticas avaliativas para maior alinhamento com a abordagem construtivista"
            ],
            comercial: [
                "Alinhar o discurso comercial com os valores pedagógicos da instituição",
                "Implementar programa de embaixadores para aumentar indicações",
                "Desenvolver material de comunicação que destaque os diferenciais pedagógicos"
            ],
            marketing: [
                "Criar conteúdo educativo que demonstre a abordagem pedagógica da instituição",
                "Desenvolver estratégia de comunicação baseada em histórias de transformação",
                "Implementar programa de relacionamento com a comunidade local"
            ],
            financeiro: [
                "Aumentar o investimento em formação continuada dos educadores",
                "Otimizar processos administrativos para reduzir custos operacionais",
                "Desenvolver fontes alternativas de receita alinhadas com a missão institucional"
            ]
        };
        
        // Construir HTML de resultados
        let html = `<h3 class="mb-4">Diagnóstico para Instituição #${instituicaoId}</h3>`;
        
        // Adicionar cada pilar selecionado
        Object.keys(pilares).forEach(pilar => {
            if (pilares[pilar]) {
                html += `<div class="result-section">
                    <h4 class="text-capitalize">${pilar}</h4>
                    <div class="row mb-3">`;
                
                // Adicionar métricas
                Object.keys(resultados[pilar]).forEach(metrica => {
                    const valor = resultados[pilar][metrica];
                    let classe = 'primary';
                    if (valor < 0.5) classe = 'danger';
                    else if (valor < 0.7) classe = 'warning';
                    else classe = 'success';
                    
                    html += `<div class="col-md-3 col-sm-6 mb-3">
                        <div class="metric-card ${valor < 0.5 ? 'danger' : valor < 0.7 ? 'warning' : 'good'}">
                            <div class="metric-value text-${classe}">${Math.round(valor * 100)}%</div>
                            <div class="metric-label">${metrica.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                        </div>
                    </div>`;
                });
                
                html += `</div>
                    <h5 class="mb-3">Recomendações</h5>
                    <div class="mb-4">`;
                
                // Adicionar recomendações
                recomendacoes[pilar].forEach(rec => {
                    html += `<div class="recommendation-item">${rec}</div>`;
                });
                
                html += `</div></div>`;
            }
        });
        
        // Adicionar botões de ação
        html += `<div class="text-end mt-4">
            <button class="btn btn-outline-secondary me-2">Exportar PDF</button>
            <button class="btn btn-primary">Compartilhar</button>
        </div>`;
        
        // Atualizar div de resultados
        resultadosDiv.innerHTML = html;
    }, 2000);
}

// Simulação de chamada à API de simulação
function simulateSimulacaoAPI(instituicaoId, cenario, horizonte, parametros) {
    // Mostrar indicador de carregamento
    const resultadosDiv = document.getElementById('simulacao-resultados');
    resultadosDiv.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div><p class="mt-3">Executando simulação...</p></div>';
    
    // Simular delay de processamento
    setTimeout(() => {
        let html = '';
        
        // Simulação para nova metodologia pedagógica
        if (cenario === 'nova_metodologia') {
            html = `<h3 class="mb-4">Simulação: Implementação de Nova Metodologia Pedagógica</h3>
            <p class="mb-4">Instituição #${instituicaoId} - Horizonte: ${horizonte} meses</p>
            
            <div class="mb-4">
                <canvas id="simulacaoChart" width="400" height="200"></canvas>
            </div>
            
            <div class="result-section">
                <h4>Análise</h4>
                <ul class="mb-4">
                    <li><strong>Engajamento dos Alunos:</strong> Crescimento consistente ao longo do período.</li>
                    <li><strong>Satisfação dos Professores:</strong> Queda inicial durante adaptação, seguida de crescimento significativo.</li>
                    <li><strong>Resultados Acadêmicos:</strong> Estabilidade inicial seguida de melhoria gradual.</li>
                </ul>
            </div>
            
            <div class="result-section">
                <h4>Recomendações</h4>
                <div class="recommendation-item">Implementar a metodologia em fases para minimizar o impacto inicial na satisfação dos professores.</div>
                <div class="recommendation-item">Oferecer suporte intensivo nos primeiros 3 meses para acelerar a adaptação.</div>
                <div class="recommendation-item">Comunicar às famílias que os resultados acadêmicos podem estabilizar antes de melhorar.</div>
            </div>
            
            <div class="text-end mt-4">
                <button class="btn btn-outline-secondary me-2">Exportar PDF</button>
                <button class="btn btn-primary">Compartilhar</button>
            </div>`;
            
            // Atualizar div de resultados
            resultadosDiv.innerHTML = html;
            
            // Criar gráfico de simulação
            const meses = Array.from({length: parseInt(horizonte)}, (_, i) => i + 1);
            const engajamento = meses.map(m => 65 + (20 * (1 - Math.exp(-0.3 * m))));
            const satisfacao = meses.map(m => 75 - 10 + (20 * (1 - Math.exp(-0.2 * m))));
            const resultados = meses.map(m => Math.max(70, 70 - 5 + (15 * (1 - Math.exp(-0.15 * (m-2))))));
            
            const simCtx = document.getElementById('simulacaoChart').getContext('2d');
            const simChart = new Chart(simCtx, {
                type: 'line',
                data: {
                    labels: meses.map(m => `Mês ${m}`),
                    datasets: [
                        {
                            label: 'Engajamento dos Alunos',
                            data: engajamento,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            tension: 0.3
                        },
                        {
                            label: 'Satisfação dos Professores',
                            data: satisfacao,
                            borderColor: '#20c997',
                            backgroundColor: 'rgba(32, 201, 151, 0.1)',
                            tension: 0.3
                        },
                        {
                            label: 'Resultados Acadêmicos',
                            data: resultados,
                            borderColor: '#fd7e14',
                            backgroundColor: 'rgba(253, 126, 20, 0.1)',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        }
        // Simulação para nova estratégia comercial
        else if (cenario === 'estrategia_comercial') {
            html = `<h3 class="mb-4">Simulação: Nova Estratégia Comercial</h3>
            <p class="mb-4">Instituição #${instituicaoId} - Horizonte: ${horizonte} meses</p>
            
            <div class="mb-4">
                <canvas id="simulacaoChart" width="400" height="200"></canvas>
            </div>
            
            <div class="result-section">
                <h4>Análise</h4>
                <ul class="mb-4">
                    <li><strong>Taxa de Conversão:</strong> Aumento significativo nos primeiros meses, seguido de estabilização.</li>
                    <li><strong>Ticket Médio:</strong> Crescimento gradual e consistente.</li>
                    <li><strong>Taxa de Renovação:</strong> Melhoria gradual, aproximando-se do limite teórico.</li>
                </ul>
            </div>
            
            <div class="result-section">
                <h4>Recomendações</h4>
                <div class="recommendation-item">Focar inicialmente na conversão de leads para capitalizar o rápido crescimento inicial.</div>
                <div class="recommendation-item">Implementar estratégias de upsell a partir do 3º mês para maximizar o ticket médio.</div>
                <div class="recommendation-item">Desenvolver programa de fidelização para sustentar a alta taxa de renovação.</div>
            </div>
            
            <div class="text-end mt-4">
                <button class="btn btn-outline-secondary me-2">Exportar PDF</button>
                <button class="btn btn-primary">Compartilhar</button>
            </div>`;
            
            // Atualizar div de resultados
            resultadosDiv.innerHTML = html;
            
            // Criar gráfico de simulação
            const meses = Array.from({length: parseInt(horizonte)}, (_, i) => i + 1);
            const conversao = meses.map(m => 22 + (15 * (1 - Math.exp(-0.5 * m))));
            const ticket = meses.map(m => 100 + (10 * (1 - Math.exp(-0.2 * m))));
            const renovacao = meses.map(m => Math.min(98, 85 + (10 * (1 - Math.exp(-0.15 * m)))));
            
            const simCtx = document.getElementById('simulacaoChart').getContext('2d');
            const simChart = new Chart(simCtx, {
                type: 'line',
                data: {
                    labels: meses.map(m => `Mês ${m}`),
                    datasets: [
                        {
                            label: 'Taxa de Conversão (%)',
                            data: conversao,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            tension: 0.3,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Ticket Médio (normalizado)',
                            data: ticket,
                            borderColor: '#20c997',
                            backgroundColor: 'rgba(32, 201, 151, 0.1)',
                            tension: 0.3,
                            yAxisID: 'y1'
                        },
                        {
                            label: 'Taxa de Renovação (%)',
                            data: renovacao,
                            borderColor: '#fd7e14',
                            backgroundColor: 'rgba(253, 126, 20, 0.1)',
                            tension: 0.3,
                            yAxisID: 'y'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            min: 0,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            min: 90,
                            max: 120,
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
        }
    }, 2000);
}

// Simulação de chamada à API do chat
function simulateChatAPI(message) {
    const chatMessages = document.getElementById('chat-messages');
    
    // Mostrar indicador de digitação
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message system-message typing-indicator';
    typingDiv.innerHTML = '<div class="message-content"><p>Digitando...</p></div>';
    chatMessages.appendChild(typingDiv);
    
    // Rolar para o final
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Simular processamento da mensagem
    setTimeout(() => {
        // Remover indicador de digitação
        chatMessages.removeChild(typingDiv);
        
        // Gerar resposta baseada na mensagem
        let resposta = '';
        
        // Palavras-chave para cada pilar
        const keywords = {
            pedagogico: ['pedagógico', 'ensino', 'aprendizagem', 'professor', 'aluno', 'aula', 'metodologia', 'avaliação', 'currículo', 'formação', 'coordenador'],
            comercial: ['comercial', 'captação', 'matrícula', 'venda', 'conversão', 'lead', 'cliente', 'preço', 'mensalidade', 'desconto'],
            marketing: ['marketing', 'marca', 'comunicação', 'redes sociais', 'campanha', 'divulgação', 'site', 'posicionamento', 'público-alvo'],
            financeiro: ['financeiro', 'orçamento', 'custo', 'receita', 'investimento', 'sustentabilidade', 'fluxo de caixa', 'inadimplência']
        };
        
        // Identificar pilar mais relevante
        let pilarRelevante = '';
        let maxScore = 0;
        
        Object.keys(keywords).forEach(pilar => {
            const score = keywords[pilar].reduce((count, keyword) => {
                return count + (message.toLowerCase().includes(keyword.toLowerCase()) ? 1 : 0);
            }, 0);
            
            if (score > maxScore) {
                maxScore = score;
                pilarRelevante = pilar;
            }
        });
        
        // Se nenhum pilar for identificado
        if (maxScore === 0) {
            resposta = "Posso ajudar com informações sobre os quatro pilares estratégicos: pedagógico, comercial, marketing e financeiro. Por favor, elabore sua pergunta com mais detalhes.";
        } else {
            // Respostas específicas para cada pilar
            switch (pilarRelevante) {
                case 'pedagogico':
                    if (message.toLowerCase().includes('coordenador')) {
                        resposta = "O coordenador pedagógico desempenha três dimensões fundamentais: articuladora, formadora e transformadora. Como articulador, conecta diferentes atores e saberes dentro da instituição. Como formador, promove o desenvolvimento profissional contínuo dos educadores. Como transformador, catalisa mudanças nas concepções e práticas educacionais.\n\nRecomendo implementar rodas de conversa como estratégia para fortalecer estas três dimensões, criando espaços de diálogo que favoreçam a autoria de pensamento.";
                    } else if (message.toLowerCase().includes('metodologia')) {
                        resposta = "A implementação de novas metodologias pedagógicas deve ser baseada em princípios construtivistas, valorizando a construção ativa do conhecimento pelos alunos. É importante considerar que este processo passa por fases de adaptação, com possível resistência inicial dos educadores.\n\nRecomendo um plano de implementação gradual, com formação continuada dos professores e acompanhamento próximo do coordenador pedagógico, utilizando narrativas docentes como ferramenta de reflexão sobre a prática.";
                    } else {
                        resposta = "O pilar pedagógico é o coração da instituição educacional, fundamentado nas três dimensões do coordenador pedagógico: articuladora, formadora e transformadora. Uma abordagem construtivista valoriza a autonomia, a construção ativa do conhecimento e a participação coletiva nos processos decisórios.\n\nRecomendo focar na formação continuada dos educadores através de rodas de conversa e documentação reflexiva dos processos educacionais.";
                    }
                    break;
                    
                case 'comercial':
                    if (message.toLowerCase().includes('captação')) {
                        resposta = "A captação de alunos deve estar alinhada com os valores educacionais da instituição. Recomendo desenvolver um discurso comercial que comunique claramente os diferenciais pedagógicos, com foco na abordagem construtivista e no desenvolvimento integral dos educandos.\n\nUm programa de embaixadores, envolvendo famílias satisfeitas com a instituição, pode aumentar significativamente as indicações qualificadas.";
                    } else if (message.toLowerCase().includes('preço') || message.toLowerCase().includes('mensalidade')) {
                        resposta = "A precificação deve equilibrar sustentabilidade financeira e compromisso social. Recomendo uma análise detalhada dos custos operacionais, com foco em eficiência sem comprometer a qualidade pedagógica.\n\nConsidere desenvolver um modelo de bolsas parciais baseado em critérios transparentes, que permita ampliar o acesso à proposta pedagógica da instituição.";
                    } else {
                        resposta = "O pilar comercial deve tratar da captação e retenção de alunos de forma alinhada com os valores educacionais. A comunicação transparente e ética dos diferenciais pedagógicos é fundamental para atrair famílias que se identifiquem com a proposta da instituição.\n\nA retenção deve ser centrada na qualidade da experiência educacional oferecida, não apenas em estratégias comerciais convencionais.";
                    }
                    break;
                    
                case 'marketing':
                    if (message.toLowerCase().includes('redes sociais')) {
                        resposta = "As redes sociais são canais poderosos para comunicar a proposta pedagógica da instituição. Recomendo criar conteúdo educativo que demonstre na prática a abordagem construtivista, compartilhando momentos significativos do cotidiano escolar, sempre respeitando a privacidade dos alunos.\n\nHistórias de transformação e depoimentos autênticos de famílias e educadores têm grande impacto na percepção da comunidade.";
                    } else if (message.toLowerCase().includes('marca')) {
                        resposta = "O posicionamento da marca deve ser baseado em valores educacionais autênticos, refletindo genuinamente a proposta pedagógica da instituição. Recomendo desenvolver uma identidade visual e verbal que comunique os princípios construtivistas e o compromisso com o desenvolvimento integral dos educandos.\n\nA coerência entre o discurso institucional e as práticas cotidianas é fundamental para a credibilidade da marca.";
                    } else {
                        resposta = "O pilar de marketing cuida da comunicação e relacionamento com a comunidade. A comunicação deve ser educativa, explicando a abordagem pedagógica da instituição de forma clara e acessível.\n\nO relacionamento com a comunidade deve ser baseado em engajamento genuíno, criando espaços de diálogo e participação que fortaleçam o sentimento de pertencimento.";
                    }
                    break;
                    
                case 'financeiro':
                    if (message.toLowerCase().includes('investimento')) {
                        resposta = "Os investimentos em formação continuada são estratégicos para a qualidade educacional. Recomendo destinar um percentual fixo do orçamento para o desenvolvimento profissional dos educadores, considerando esta uma prioridade institucional.\n\nA análise de retorno sobre investimento deve considerar não apenas métricas financeiras, mas também o impacto na qualidade pedagógica e na satisfação da comunidade escolar.";
                    } else if (message.toLowerCase().includes('sustentabilidade')) {
                        resposta = "A sustentabilidade institucional requer equilíbrio entre impacto social e viabilidade econômica. Recomendo desenvolver um planejamento financeiro de longo prazo, alinhado com o projeto pedagógico da instituição.\n\nConsidere diversificar fontes de receita através de serviços complementares que estejam alinhados com a missão educacional, como cursos de extensão, formação para educadores de outras instituições ou parcerias estratégicas.";
                    } else {
                        resposta = "O pilar financeiro busca a sustentabilidade institucional a serviço do projeto pedagógico. A gestão financeira deve estar alinhada com as prioridades pedagógicas, garantindo recursos adequados para a qualidade educacional.\n\nA transparência na gestão financeira fortalece a confiança da comunidade e contribui para decisões mais conscientes e participativas.";
                    }
                    break;
            }
            
            // Adicionar referência ao pilar
            resposta += `\n\nEsta resposta está relacionada principalmente ao pilar ${pilarRelevante}.`;
        }
        
        // Adicionar mensagem ao chat
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message system-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Processar quebras de linha
        const paragraphs = resposta.split('\n').filter(p => p.trim() !== '');
        paragraphs.forEach(paragraph => {
            const p = document.createElement('p');
            p.textContent = paragraph;
            contentDiv.appendChild(p);
        });
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Rolar para o final
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 1500);
}

// Configuração de segurança
function setupSecurity() {
    // Implementar proteção contra XSS
    function sanitizeInput(input) {
        const temp = document.createElement('div');
        temp.textContent = input;
        return temp.innerHTML;
    }
    
    // Implementar proteção contra CSRF
    const csrfToken = generateCSRFToken();
    
    // Adicionar token CSRF a todas as requisições AJAX
    function addCSRFTokenToRequests() {
        // Interceptar todas as requisições fetch
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            
            // Adicionar token CSRF ao cabeçalho
            options.headers['X-CSRF-Token'] = csrfToken;
            
            return originalFetch.call(this, url, options);
        };
    }
    
    // Gerar token CSRF
    function generateCSRFToken() {
        return Array.from(window.crypto.getRandomValues(new Uint8Array(16)))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
    
    // Implementar proteção contra clickjacking
    function preventClickjacking() {
        if (window.self !== window.top) {
            // A página está em um iframe
            window.top.location = window.self.location;
        }
    }
    
    // Implementar validação de entrada
    function setupInputValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                // Validar todos os campos do formulário
                const inputs = form.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    if (input.value) {
                        input.value = sanitizeInput(input.value);
                    }
                });
            });
        });
    }
    
    // Implementar proteção de sessão
    function setupSessionProtection() {
        // Simular verificação de inatividade
        let inactivityTimeout;
        
        function resetInactivityTimer() {
            clearTimeout(inactivityTimeout);
            inactivityTimeout = setTimeout(logoutDueToInactivity, 30 * 60 * 1000); // 30 minutos
        }
        
        function logoutDueToInactivity() {
            // Simular logout
            alert('Sua sessão expirou devido à inatividade. Por favor, faça login novamente.');
            // Redirecionar para página de login (simulado)
            // window.location.href = 'login.html';
        }
        
        // Resetar timer em eventos de usuário
        ['mousedown', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetInactivityTimer);
        });
        
        // Iniciar timer
        resetInactivityTimer();
    }
    
    // Executar configurações de segurança
    addCSRFTokenToRequests();
    preventClickjacking();
    setupInputValidation();
    setupSessionProtection();
}
