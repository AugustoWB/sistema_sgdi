(function () {
    var form = document.getElementById('filtros-gerenciamento');

    if (!form) {
        return;
    }

    var pedido = null;

    form.addEventListener('change', function () {
        atualizar();
    });

    form.addEventListener('submit', function (evento) {
        evento.preventDefault();
        atualizar();
    });

    function parametrosDoFormulario() {
        var dados = new FormData(form);
        var params = new URLSearchParams();

        dados.forEach(function (valor, chave) {
            if (String(valor).trim() !== '') {
                params.set(chave, valor);
            }
        });

        return params;
    }

    function atualizar() {
        var params = parametrosDoFormulario();
        var consulta = params.toString();
        var urlApi = '/api/gerenciamento' + (consulta ? '?' + consulta : '');

        if (pedido) {
            pedido.abort();
        }

        pedido = new AbortController();

        fetch(urlApi, { signal: pedido.signal })
            .then(function (resposta) {
                if (!resposta.ok) {
                    throw new Error('Falha ao carregar os indicadores');
                }
                return resposta.json();
            })
            .then(function (dados) {
                desenhar(dados, params);
                var pagina = '/gerenciamento' + (consulta ? '?' + consulta : '');
                history.replaceState(null, '', pagina);
            })
            .catch(function (erro) {
                if (erro.name !== 'AbortError') {
                    form.submit();
                }
            });
    }

    function desenhar(dados, params) {
        texto('kpi-total', dados.total);
        texto('kpi-abertas', dados.abertas);
        texto('kpi-concluidas', dados.concluidas);
        texto('kpi-atrasadas', dados.atrasadas);
        texto('kpi-criticas', dados.criticas);
        texto('kpi-tempo', dados.tempoMedioResolucao || '—');
        texto(
            'kpi-abertas-nota',
            dados.statusAberta + ' com status aberta e ' + dados.emAndamento + ' em andamento'
        );
        texto(
            'kpi-total-nota',
            params.toString() ? 'Demandas do filtro atual' : 'Todas as demandas cadastradas'
        );
        texto(
            'kpi-tempo-nota',
            dados.tempoMedioResolucao
                ? 'Da criação até a conclusão'
                : 'Nenhuma concluída com data de conclusão'
        );
        texto(
            'kpi-escopo',
            params.toString()
                ? 'Exibindo ' + dados.total + ' demanda(s) do filtro atual.'
                : 'Exibindo todas as ' + dados.total + ' demandas.'
        );

        var complemento = [];
        if (dados.canceladas) {
            complemento.push('Canceladas: ' + dados.canceladas + '.');
        }
        if (dados.concluidasSemData) {
            complemento.push(
                dados.concluidasSemData
                + ' concluída(s) ainda sem data de conclusão e fora do tempo médio.'
            );
        }
        texto('kpi-complemento', complemento.join(' '));

        var link = document.getElementById('link-concluidas');
        if (link) {
            var extra = new URLSearchParams(params);
            extra.set('status', 'concluida');
            link.href = '/?' + extra.toString();
        }

        preencherBarras(
            document.getElementById('grafico-status'),
            dados.porStatus,
            'valor',
            'rotulo'
        );
        preencherBarras(
            document.getElementById('grafico-prioridade'),
            dados.porPrioridade,
            'valor',
            'rotulo'
        );
        preencherBarras(
            document.getElementById('grafico-responsavel'),
            dados.porResponsavel.map(function (linha) {
                return {
                    rotulo: linha.nome,
                    valor: linha.total,
                    cor: linha.cor || '#333333',
                    largura: linha.largura
                };
            }),
            'valor',
            'rotulo'
        );
        preencherTabela(dados.porResponsavel, params);
    }

    function texto(id, valor) {
        var elemento = document.getElementById(id);
        if (elemento) {
            elemento.textContent = valor;
        }
    }

    function preencherBarras(lista, itens) {
        if (!lista) {
            return;
        }

        lista.replaceChildren();

        if (!itens.length) {
            var vazio = document.createElement('li');
            vazio.className = 'barra-vazia';
            vazio.textContent = 'Nenhuma demanda neste filtro.';
            lista.appendChild(vazio);
            return;
        }

        itens.forEach(function (item) {
            var linha = document.createElement('li');
            var rotulo = document.createElement('span');
            rotulo.className = 'barra-rotulo';
            rotulo.textContent = item.rotulo;

            var trilho = document.createElement('span');
            trilho.className = 'barra-trilho';
            trilho.setAttribute('aria-hidden', 'true');

            var preenchimento = document.createElement('span');
            preenchimento.className = 'barra-preenchimento';
            preenchimento.style.width = (item.largura || 0) + '%';
            preenchimento.style.background = item.cor;

            var valor = document.createElement('span');
            valor.className = 'barra-valor';
            valor.textContent = item.valor;

            trilho.appendChild(preenchimento);
            linha.appendChild(rotulo);
            linha.appendChild(trilho);
            linha.appendChild(valor);
            lista.appendChild(linha);
        });
    }

    function preencherTabela(linhas, params) {
        var corpo = document.getElementById('corpo-responsaveis');
        if (!corpo) {
            return;
        }

        corpo.replaceChildren();

        if (!linhas.length) {
            var tr = document.createElement('tr');
            var td = document.createElement('td');
            td.colSpan = 6;
            td.style.textAlign = 'center';
            td.textContent = params.toString()
                ? 'Nenhuma demanda encontrada com estes filtros.'
                : 'Nenhuma demanda cadastrada.';
            tr.appendChild(td);
            corpo.appendChild(tr);
            return;
        }

        linhas.forEach(function (linha) {
            var tr = document.createElement('tr');
            var nome = document.createElement('td');

            if (linha.id) {
                var link = document.createElement('a');
                var consulta = new URLSearchParams();
                consulta.set('responsibleId', linha.id);
                if (params.get('status')) {
                    consulta.set('status', params.get('status'));
                }
                if (params.get('priority')) {
                    consulta.set('priority', params.get('priority'));
                }
                link.href = '/?' + consulta.toString();
                link.textContent = linha.nome;
                nome.appendChild(link);
            } else {
                nome.textContent = linha.nome;
            }

            tr.appendChild(nome);
            [linha.total, linha.abertas, linha.concluidas, linha.atrasadas, linha.criticas]
                .forEach(function (numero) {
                    var celula = document.createElement('td');
                    celula.textContent = numero;
                    tr.appendChild(celula);
                });
            corpo.appendChild(tr);
        });
    }
}());
