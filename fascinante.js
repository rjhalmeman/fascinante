// Array que funcionará como nosso "banco de dados" em memória
let registros = [];

// Captura os botões da tela
const btnExtrair = document.getElementById('btnExtrair');
const btnSalvar = document.getElementById('btnSalvar');
const fileInput = document.getElementById('fileInput');

// Eventos
btnExtrair.addEventListener('click', extrairDados);
btnSalvar.addEventListener('click', exportarCSV);
fileInput.addEventListener('change', importarCSV);

/**
 * Função para gerar data e hora no formato yyyy-mm-dd-HH-mm-ss
 */
function gerarDataHora() {
    const agora = new Date();
    const yyyy = agora.getFullYear();
    const mm = String(agora.getMonth() + 1).padStart(2, '0');
    const dd = String(agora.getDate()).padStart(2, '0');
    const HH = String(agora.getHours()).padStart(2, '0');
    const min = String(agora.getMinutes()).padStart(2, '0');
    const ss = String(agora.getSeconds()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}-${HH}-${min}-${ss}`;
}

/**
 * CREATE: Extrai os dados do texto e adiciona ao array (CRUD)
 */
function extrairDados() {
    const texto = document.getElementById('inputText').value;
    
    if (!texto.trim()) {
        alert('Por favor, cole o texto na caixa antes de extrair.');
        return;
    }

    let assuntoExtraido = "";
    let linkExtraido = "";

    // Expressão regular para tentar capturar o que está entre aspas após "Assista a"
    const matchAssunto = texto.match(/Assista a "(.*?)"/i);
    if (matchAssunto && matchAssunto[1]) {
        assuntoExtraido = matchAssunto[1];
    } else {
        // Fallback: pega a primeira linha não vazia do texto
        const linhas = texto.split('\n').filter(l => l.trim() !== '');
        if (linhas.length > 0) assuntoExtraido = linhas[0].trim();
    }

    // Expressão regular para capturar URLs
    const matchLink = texto.match(/(https?:\/\/[^\s]+)/);
    if (matchLink && matchLink[0]) {
        linkExtraido = matchLink[0];
    }

    if (!assuntoExtraido && !linkExtraido) {
        alert('Não foi possível identificar o assunto ou o link no formato fornecido.');
        return;
    }

    // Cria o objeto
    const novoRegistro = {
        datahora: gerarDataHora(),
        assunto: assuntoExtraido,
        link: linkExtraido,
        texto_complementar: ""
    };

    // Adiciona no array e atualiza a tela
    registros.push(novoRegistro);
    renderizarTabela();
    
    // Limpa a caixa de texto
    document.getElementById('inputText').value = '';
}

/**
 * READ: Renderiza a tabela na tela (CRUD)
 */
function renderizarTabela() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = ''; // Limpa a tabela atual

    registros.forEach((registro, index) => {
        const tr = document.createElement('tr');
        
        // Criamos inputs diretamente nas células para facilitar a Edição (UPDATE)
        tr.innerHTML = `
            <td>${registro.datahora}</td>
            <td>
                <input type="text" value="${registro.assunto}" 
                       onchange="atualizarRegistro(${index}, 'assunto', this.value)">
            </td>
            <td>
                <input type="text" value="${registro.link}" 
                       onchange="atualizarRegistro(${index}, 'link', this.value)">
            </td>
            <td>
                <input type="text" value="${registro.texto_complementar}" placeholder="Opcional..."
                       onchange="atualizarRegistro(${index}, 'texto_complementar', this.value)">
            </td>
            <td>
                <button class="btn-excluir" onclick="excluirRegistro(${index})">Excluir</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * UPDATE: Atualiza um registro no array (acionado ao digitar na tabela)
 */
window.atualizarRegistro = function(index, campo, valor) {
    registros[index][campo] = valor;
}

/**
 * DELETE: Exclui um registro da tabela e do array (CRUD)
 */
window.excluirRegistro = function(index) {
    if(confirm('Tem certeza que deseja excluir este registro?')) {
        registros.splice(index, 1);
        renderizarTabela();
    }
}

/**
 * Exporta os registros em memória para um arquivo .csv
 */
function exportarCSV() {
    if (registros.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }

    // Cabeçalho do CSV
    let conteudoCSV = "datahora;assunto;link;texto_complementar\n";

    registros.forEach(r => {
        // Remove quebras de linha e trata aspas para evitar quebrar o CSV
        const datahora = r.datahora;
        const assunto = `"${(r.assunto || '').replace(/"/g, '""')}"`;
        const link = `"${(r.link || '').replace(/"/g, '""')}"`;
        const texto = `"${(r.texto_complementar || '').replace(/"/g, '""')}"`;

        conteudoCSV += `${datahora};${assunto};${link};${texto}\n`;
    });

    // Cria o download via Blob
    const blob = new Blob(["\uFEFF" + conteudoCSV], { type: 'text/csv;charset=utf-8;' }); // \uFEFF força o BOM para o Excel ler acentos
    const url = URL.createObjectURL(blob);
    const linkTag = document.createElement("a");
    linkTag.href = url;
    linkTag.download = `dados_extraidos_${gerarDataHora()}.csv`;
    linkTag.click();
    URL.revokeObjectURL(url);
}

/**
 * Importa um arquivo .csv previamente salvo e o carrega na memória
 */
function importarCSV(event) {
    const arquivo = event.target.files[0];
    if (!arquivo) return;

    const leitor = new FileReader();
    leitor.onload = function(e) {
        const conteudo = e.target.result;
        // Divide o arquivo por linhas
        const linhas = conteudo.split('\n').filter(linha => linha.trim() !== '');
        
        if (linhas.length <= 1) {
            alert('Arquivo CSV vazio ou inválido.');
            return;
        }

        registros = []; // Zera a lista atual

        // Pula a primeira linha (cabeçalho)
        for (let i = 1; i < linhas.length; i++) {
            // Dividir por ponto e vírgula. Uma função básica para extrair dados entre aspas.
            const colunas = parseLinhaCSV(linhas[i]);
            
            if (colunas.length >= 3) {
                registros.push({
                    datahora: colunas[0].replace(/^"|"$/g, ''),
                    assunto: colunas[1].replace(/^"|"$/g, ''),
                    link: colunas[2].replace(/^"|"$/g, ''),
                    texto_complementar: colunas[3] ? colunas[3].replace(/^"|"$/g, '') : ''
                });
            }
        }
        renderizarTabela();
        
        // Limpa o input file para permitir importar o mesmo arquivo novamente, se necessário
        fileInput.value = ''; 
    };
    
    leitor.readAsText(arquivo, 'utf-8');
}

/**
 * Função de apoio didática para dividir linhas CSV ignorando ponto e vírgulas dentro das aspas
 */
function parseLinhaCSV(linha) {
    let dentroAspas = false;
    let colunas = [];
    let valorAtual = '';

    for (let i = 0; i < linha.length; i++) {
        const char = linha[i];
        
        if (char === '"') {
            dentroAspas = !dentroAspas;
        } else if (char === ';' && !dentroAspas) {
            colunas.push(valorAtual);
            valorAtual = '';
            continue;
        }
        valorAtual += char;
    }
    colunas.push(valorAtual);
    return colunas;
}