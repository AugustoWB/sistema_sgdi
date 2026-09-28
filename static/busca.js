(function () {
    var form = document.getElementById('form-busca');
    var campo = document.getElementById('campo-busca');

    if (!form || !campo) {
        return;
    }

    var DEBOUNCE_MS = 400;
    var timer = null;
    var controle = null;
    var ultimoEnviado = campo.value.trim();

    function tabela() {
        return document.getElementById('tabela-demandas');
    }

    function limiteAtual() {
        var select = document.getElementById('limit');
        return select ? select.value : '20';
    }

    var ROTULOS_STATUS = {
        aberta: 'Aberta',
        em_andamento: 'Em Andamento',
        concluida: 'Concluída',
        cancelada: 'Cancelada'
    };

    function valorCampo(id) {
        var campoFiltro = document.getElementById(id);
        return campoFiltro ? campoFiltro.value : '';
    }

    function filtrosAtivos() {
        return Boolean(
            valorCampo('status')
            || valorCampo('priority') !== ''
            || valorCampo('responsibleId')
        );
    }

    function aplicarFiltros(params) {
        var status = valorCampo('status');
        var priority = valorCampo('priority');
        var responsibleId = valorCampo('responsibleId');
        var usuario = valorCampo('usuario_id');

        if (status) {
            params.set('status', status);
        }

        if (priority !== '') {
            params.set('priority', priority);
        }

        if (responsibleId) {
            params.set('responsibleId', responsibleId);
        }

        if (usuario) {
            params.set('usuario_id', usuario);
        }
    }

    function urlDaApi(q) {
        var params = new URLSearchParams();
        params.set('page', '1');
        params.set('limit', limiteAtual());
        aplicarFiltros(params);

        if (q) {
            params.set('q', q);
        }

        return '/api/demandas?' + params.toString();
    }

    function hrefDaPagina(numero, q) {
        var params = new URLSearchParams();
        params.set('page', String(numero));
        params.set('limit', limiteAtual());
        aplicarFiltros(params);

        if (q) {
            params.set('q', q);
        }

        return window.location.pathname + '?' + params.toString();
    }

    function janelaDePaginas(atual, total) {
        var tamanho = 5;
        var paginas = [];
        var inicio;
        var fim;
        var numero;

        if (total <= 0) {
            return paginas;
        }

        if (total <= tamanho) {
            for (numero = 1; numero <= total; numero += 1) {
                paginas.push(numero);
            }
            return paginas;
        }

        inicio = Math.max(1, atual - Math.floor(tamanho / 2));
        fim = Math.min(total, inicio + tamanho - 1);
        inicio = Math.max(1, fim - tamanho + 1);

        for (numero = inicio; numero <= fim; numero += 1) {
            paginas.push(numero);
        }

        return paginas;
    }

    function limpar(elemento) {
        while (elemento.firstChild) {
            elemento.removeChild(elemento.firstChild);
        }
    }

    function celula(texto) {
        var td = document.createElement('td');
        td.textContent = texto == null ? '' : String(texto);
        return td;
    }

    function linkAcao(href, texto, cor) {
        var link = document.createElement('a');
        link.href = href;
        link.textContent = texto;
        if (cor) {
            link.style.color = cor;
        }
        return link;
    }

    function spanPrioridade(priority) {
        var span = document.createElement('span');

        if (priority === 3) {
            span.style.color = 'red';
            span.style.fontWeight = 'bold';
            span.textContent = 'Alta';
        } else if (priority === 2) {
            span.style.color = 'orange';
            span.style.fontWeight = 'bold';
            span.textContent = 'Média';
        } else if (priority === 1) {
            span.style.color = 'blue';
            span.style.fontWeight = 'bold';
            span.textContent = 'Baixa';
        } else {
            span.style.color = 'gray';
            span.textContent = 'Nenhuma';
        }

        return span;
    }

    function linhaDaDemanda(demanda) {
        var tr = document.createElement('tr');
        var prioridade = document.createElement('td');
        var acoes = document.createElement('td');
        var deletar = linkAcao('/deletar/' + demanda.id, 'Deletar', 'red');

        tr.appendChild(celula(demanda.id));
        tr.appendChild(celula(demanda.titulo));
        tr.appendChild(celula(demanda.solicitante));
        tr.appendChild(celula(demanda.data_criacao));
        prioridade.appendChild(spanPrioridade(demanda.priority));
        tr.appendChild(prioridade);
        tr.appendChild(celula(ROTULOS_STATUS[demanda.status] || demanda.status || ''));
        tr.appendChild(celula(demanda.responsavel));

        deletar.onclick = function () {
            return confirm('Tem certeza que deseja deletar esta demanda?');
        };

        acoes.appendChild(linkAcao('/detalhes/' + demanda.id, 'Ver'));
        acoes.appendChild(document.createTextNode(' | '));
        acoes.appendChild(linkAcao('/editar/' + demanda.id, 'Editar'));
        acoes.appendChild(document.createTextNode(' | '));
        acoes.appendChild(deletar);
        tr.appendChild(acoes);

        return tr;
    }

    function linhaVazia() {
        var tr = document.createElement('tr');
        var td = document.createElement('td');
        td.colSpan = 8;
        td.style.textAlign = 'center';
        td.textContent = filtrosAtivos()
            ? 'Nenhuma demanda encontrada com estes filtros'
            : 'Nenhuma demanda encontrada.';
        tr.appendChild(td);
        return tr;
    }

    function adicionarLink(nav, texto, href) {
        var link = document.createElement('a');
        link.textContent = texto;
        link.href = href;
        nav.appendChild(link);
    }

    function adicionarSpan(nav, texto, classe) {
        var span = document.createElement('span');
        span.textContent = texto;
        span.className = classe;
        nav.appendChild(span);
    }

    function atualizarPaginacao(dados, q) {
        var info = document.getElementById('paginacao-info');
        var nav = document.getElementById('paginacao-controles');
        var limite = Number(limiteAtual());
        var total = dados.totalItems;
        var atual = dados.currentPage;
        var paginas;
        var indice;
        var inicio;
        var fim;

        if (!info || !nav) {
            return;
        }

        if (!total) {
            info.textContent = 'Exibindo 0 de 0';
        } else {
            inicio = (atual - 1) * limite + 1;
            fim = inicio + dados.demandas.length - 1;
            info.textContent = 'Exibindo ' + inicio + '-' + fim + ' de ' + total;
        }

        limpar(nav);

        if (atual > 1 && dados.totalPages > 0) {
            adicionarLink(nav, 'Anterior', hrefDaPagina(atual - 1, q));
        } else {
            adicionarSpan(nav, 'Anterior', 'desabilitado');
        }

        paginas = janelaDePaginas(atual, dados.totalPages);

        if (paginas.length && paginas[0] > 1) {
            adicionarLink(nav, '1', hrefDaPagina(1, q));
            if (paginas[0] > 2) {
                adicionarSpan(nav, '…', 'reticencias');
            }
        }

        for (indice = 0; indice < paginas.length; indice += 1) {
            if (paginas[indice] === atual) {
                adicionarSpan(nav, String(paginas[indice]), 'ativa');
                nav.lastChild.setAttribute('aria-current', 'page');
            } else {
                adicionarLink(nav, String(paginas[indice]), hrefDaPagina(paginas[indice], q));
            }
        }

        if (paginas.length && paginas[paginas.length - 1] < dados.totalPages) {
            if (paginas[paginas.length - 1] < dados.totalPages - 1) {
                adicionarSpan(nav, '…', 'reticencias');
            }
            adicionarLink(nav, String(dados.totalPages), hrefDaPagina(dados.totalPages, q));
        }

        if (atual < dados.totalPages) {
            adicionarLink(nav, 'Próxima', hrefDaPagina(atual + 1, q));
        } else {
            adicionarSpan(nav, 'Próxima', 'desabilitado');
        }
    }

    function guardarTermo(q) {
        var campos = [
            document.getElementById('q-filtro'),
            document.getElementById('q-paginacao')
        ];
        var indice;

        for (indice = 0; indice < campos.length; indice += 1) {
            if (campos[indice]) {
                campos[indice].value = q;
            }
        }
    }

    function atualizarEndereco(q) {
        var params = new URLSearchParams(window.location.search);
        params.set('page', '1');
        params.set('limit', limiteAtual());
        params.delete('status');
        params.delete('priority');
        params.delete('responsibleId');
        params.delete('usuario_id');
        aplicarFiltros(params);

        if (q) {
            params.set('q', q);
        } else {
            params.delete('q');
        }

        window.history.replaceState(null, '', window.location.pathname + '?' + params.toString());
    }

    function renderizar(dados, q) {
        var corpo = document.querySelector('#tabela-demandas tbody');
        var indice;

        if (!corpo) {
            return;
        }

        limpar(corpo);

        if (!dados.demandas.length) {
            corpo.appendChild(linhaVazia());
        } else {
            for (indice = 0; indice < dados.demandas.length; indice += 1) {
                corpo.appendChild(linhaDaDemanda(dados.demandas[indice]));
            }
        }

        guardarTermo(q);
        atualizarPaginacao(dados, q);
        atualizarEndereco(q);
    }

    function executar(forcar) {
        var q = campo.value.trim();

        if (!tabela()) {
            if (forcar || q !== ultimoEnviado) {
                ultimoEnviado = q;
                form.submit();
            }
            return;
        }

        if (!forcar && q === ultimoEnviado) {
            return;
        }

        if (controle) {
            controle.abort();
        }

        controle = new AbortController();

        fetch(urlDaApi(q), { signal: controle.signal })
            .then(function (resposta) {
                if (!resposta.ok) {
                    throw new Error('Falha na busca');
                }
                return resposta.json();
            })
            .then(function (dados) {
                if (campo.value.trim() !== q) {
                    return;
                }
                ultimoEnviado = q;
                renderizar(dados, q);
            })
            .catch(function (erro) {
                if (erro.name === 'AbortError') {
                    return;
                }
            });
    }

    function omitirCamposVazios(formulario) {
        if (!formulario) {
            return;
        }

        formulario.addEventListener('submit', function () {
            var campos = formulario.querySelectorAll('input, select');
            var indice;

            for (indice = 0; indice < campos.length; indice += 1) {
                if (campos[indice].value === '') {
                    campos[indice].disabled = true;
                }
            }
        });
    }

    omitirCamposVazios(document.querySelector('form.filtros'));
    omitirCamposVazios(document.querySelector('form.paginacao-tamanho'));

    campo.addEventListener('input', function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
            executar(false);
        }, DEBOUNCE_MS);
    });

    form.addEventListener('submit', function (evento) {
        window.clearTimeout(timer);

        if (!tabela()) {
            return;
        }

        evento.preventDefault();
        executar(true);
    });
})();
