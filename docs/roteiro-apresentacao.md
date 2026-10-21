# Roteiro de apresentação — SGDI

Três funcionalidades, nesta ordem. Antes de começar, abra http://127.0.0.1:5000 com o sistema no ar (`python app.py`). Deixe a tela em **Início** e os filtros da área de gerenciamento limpos.

Tempo sugerido: cerca de 8 minutos no total.

---

## 1. Área de gerenciamento e indicadores

**Tempo:** 3 minutos.

**O que mostrar:** o menu **Gerenciamento** e os seis números da tela.

**Falar:**

> A listagem mostra demanda por demanda. A área de gerenciamento responde outra pergunta: como está o conjunto inteiro.
>
> Aqui entram os números gerais do sistema. O total é tudo o que está cadastrado. Abertas reúnem o que ainda não terminou: status aberta e em andamento. Concluídas são as que já foram encerradas com sucesso. Atrasadas são as abertas criadas há mais de 30 dias. Críticas são as de prioridade alta que ainda estão em aberto. O tempo médio de resolução mede o intervalo entre a criação e a data em que a demanda foi concluída.
>
> Abaixo dos cartões, a tabela reparte esses mesmos números por responsável. O nome abre a listagem só daquela pessoa.

**Demonstrar:**

1. No menu, clique em **Gerenciamento**.
2. Aponte, nesta ordem: **Total de demandas**, **Abertas**, **Concluídas**, **Atrasadas**, **Críticas** e **Tempo médio de resolução**.
3. Role até **Detalhamento por responsável** e mostre as colunas Total, Abertas, Concluídas, Atrasadas e Críticas.
4. Clique no nome de um responsável e mostre a listagem filtrada. Volte em **Gerenciamento**.

**Se perguntarem:**

- Aberta e em andamento contam juntas em **Abertas**. O texto do cartão separa as duas quantidades.
- Atraso usa o prazo de 30 dias a partir da data de criação. Demanda concluída ou cancelada não entra como atrasada.
- Crítica é prioridade alta ainda em aberto. Concluída de prioridade alta não entra nesse número.
- O tempo médio só usa demandas concluídas que já têm data de conclusão. Essa data é gravada quando a demanda passa para concluída.

---

## 2. Gráficos que acompanham o filtro

**Tempo:** 2 minutos e meio.

**O que mostrar:** os três gráficos e a mudança ao filtrar.

**Falar:**

> Os mesmos números aparecem em gráfico, para comparar situação, prioridade e carga de cada responsável.
>
> O filtro é o da própria tela: status, prioridade e responsável. Dá para usar um só ou os três juntos. Ao escolher um valor, os cartões, os gráficos e a tabela são recalculados com esse recorte. A barra maior da série é a referência; as outras ficam proporcionais a ela.

**Demonstrar:**

1. Ainda em **Gerenciamento**, mostre os gráficos **Por status**, **Por prioridade** e **Por responsável**.
2. Em **Prioridade**, escolha **Alta**. Espere a tela atualizar sem clicar em Filtrar.
3. Aponte que o gráfico de prioridade concentra a barra em Alta e que o total do cartão diminuiu.
4. Em **Responsável**, escolha uma pessoa que apareça no gráfico. Mostre que o gráfico de responsável fica só com ela e que a tabela acompanha.
5. Clique em **Limpar filtros** e confirme que os números gerais voltam.

**Se perguntarem:**

- O filtro também pode ser aplicado pelo botão **Filtrar**. Mudar o campo já atualiza a tela.
- A URL guarda o filtro. Recarregar a página mantém o mesmo recorte.
- Status, prioridade e responsável se combinam: a demanda precisa atender a todos os filtros escolhidos.

---

## 3. Exportação em PDF e Excel

**Tempo:** 2 minutos e meio.

**O que mostrar:** os botões **Exportar PDF** e **Exportar Excel**, e que o arquivo usa o filtro da tela.

**Falar:**

> O relatório pode sair da tela em PDF ou em Excel. Os dois botões enviam os filtros que estão selecionados agora. O arquivo não é um retrato de todas as demandas se a tela estiver filtrada: ele repete o recorte do dashboard.
>
> No cabeçalho ficam o nome da empresa, SGDI, e a data e a hora em que o relatório foi gerado. No rodapé, os filtros aparecem por extenso. Mesmo quando um filtro está em Todos, ele é escrito, para ficar claro o que entrou e o que ficou de fora.

**Demonstrar:**

1. Com os filtros limpos, diga que o rodapé vai dizer status Todos, prioridade Todas e responsável Todos.
2. Selecione um status, por exemplo **Concluída**, e um responsável.
3. Espere o total da tela mudar. Leia esse número em voz alta.
4. Clique em **Exportar Excel**. Abra o arquivo.
5. Mostre o cabeçalho: **SGDI** e **Data de geração**.
6. Mostre que o total de demandas do arquivo é o mesmo número da tela.
7. Role até o final e leia o rodapé: `Filtros aplicados: Status: ... | Prioridade: ... | Responsável: ...`.
8. Volte à tela e clique em **Exportar PDF**. Mostre o mesmo cabeçalho e o mesmo rodapé.

**Se perguntarem:**

- PDF e Excel levam as mesmas tabelas: indicadores, status, prioridade e responsável.
- O nome do arquivo inclui a data e a hora da geração.
- No Excel, cabeçalho e rodapé também valem para a impressão da planilha.
- Limpar o filtro e exportar de novo gera o relatório do conjunto completo, e o rodapé registra Todos.
