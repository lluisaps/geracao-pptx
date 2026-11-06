const { embedQuerySuffix } = require('../../../config/embedMode');
const { getGlobalScripts } = require('../../../core/globalScripts');

const STYLES = `
:root{--azul:#0BBBEF;--escuro:#0b1720;--borda:#d9e2e8;--texto:#1d2a33;--suave:#5d6d78;--alerta:#b45309;--alerta-fundo:#fff7e6;--ok:#047857}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f3f6f8;color:var(--texto)}
.header-nav{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;background:var(--escuro)}
.home-button{color:#fff;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:8px;background:rgba(255,255,255,.08)}
.home-button:hover{background:rgba(255,255,255,.16)}
body.embed .header-nav{display:none}
.container{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:24px;margin:0 0 4px}h1 span{color:var(--azul)}
.sub{color:var(--suave);margin:0 0 20px;font-size:14px}
.passo{background:#fff;border:1px solid var(--borda);border-radius:14px;padding:20px;margin-bottom:18px}
.passo h2{font-size:16px;margin:0 0 14px;display:flex;align-items:center;gap:10px}
.num{display:inline-flex;width:26px;height:26px;border-radius:50%;background:var(--azul);color:#fff;font-size:13px;align-items:center;justify-content:center}
.passo.inativo{opacity:.45;pointer-events:none}
.grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.grade.dois{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
label{display:block;font-size:12px;font-weight:600;color:var(--suave);margin-bottom:4px}
input,textarea,select{width:100%;padding:9px 10px;border:1px solid var(--borda);border-radius:8px;font:inherit;font-size:14px;background:#fff;color:var(--texto)}
textarea{min-height:74px;resize:vertical}
.campo{margin-bottom:12px}
.ajuda{font-size:12px;color:var(--suave);margin-top:3px}
.revisar{border-color:var(--alerta);background:var(--alerta-fundo)}
button{background:var(--azul);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:14px;font-weight:600;cursor:pointer}
button[disabled]{background:#9fb3bf;cursor:not-allowed}
button.secundario{background:#fff;color:var(--texto);border:1px solid var(--borda)}
.acoes{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:6px}
.status{font-size:13px;color:var(--suave)}
.status.erro{color:#b91c1c}.status.ok{color:var(--ok)}
.resumo{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:4px 0 16px}
.cartao{background:var(--escuro);color:#fff;border-radius:10px;padding:12px}
.cartao b{display:block;color:var(--azul);font-size:20px}
.cartao span{font-size:12px;opacity:.85}
details{margin-top:10px}summary{cursor:pointer;font-size:13px;color:var(--suave)}
pre{background:#0f1c25;color:#d6e2ea;padding:12px;border-radius:8px;font-size:11.5px;max-height:360px;overflow:auto;white-space:pre-wrap}
.slides{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:14px}
.slides img{width:100%;border-radius:8px;border:1px solid var(--borda);display:block}
.slides figcaption{font-size:12px;color:var(--suave);margin-top:4px}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}
.pill.alerta{background:var(--alerta-fundo);color:var(--alerta)}.pill.ok{background:#e7f8f1;color:var(--ok)}
.check{display:flex;gap:16px;flex-wrap:wrap;font-size:14px}.check label{display:flex;gap:6px;align-items:center;font-weight:400;color:var(--texto);font-size:14px}
.check input{width:auto}
@media (max-width:600px){.container{padding:16px}}
`;

const SCRIPT = `
(function(){
  var BASE = '/gerador-ate/api';
  var trabalho = null, params = null;
  var $ = function(id){ return document.getElementById(id); };

  // nomes padrão dos tópicos quando o montar.py deixa REVISAR no título
  var TOPICOS = {
    melhorias: ['O que foi entregue no robô', 'O que fizemos para evitar falhas'],
    proximas_evolucoes: ['Próximas evoluções', 'Oportunidades no segmento']
  };

  function status(el, texto, tipo){ el.textContent = texto; el.className = 'status' + (tipo ? ' ' + tipo : ''); }
  function linhas(t){ return t.split('\\n').map(function(x){ return x.trim(); }).filter(Boolean); }
  function fmt(n){ return (n == null) ? '—' : Number(n).toLocaleString('pt-BR'); }

  async function chamar(metodo, url, corpo){
    var r = await fetch(url, { method: metodo, headers: { 'Content-Type': 'application/json' },
      body: corpo ? JSON.stringify(corpo) : undefined, credentials: 'same-origin' });
    var j = await r.json().catch(function(){ return { erro: 'resposta inválida (' + r.status + ')' }; });
    if (!r.ok) throw new Error(j.erro || ('HTTP ' + r.status));
    return j;
  }

  // ---------------------------------------------------------------- passo 1
  $('form-buscar').addEventListener('submit', async function(ev){
    ev.preventDefault();
    var st = $('st-buscar'); $('btn-buscar').disabled = true;
    status(st, 'Consultando planilha, vault, banco e GLPI… (pode levar 1–2 min)');
    $('passo2').classList.add('inativo'); $('passo3').classList.add('inativo');
    try {
      var j = await chamar('POST', BASE + '/montar', {
        cliente: $('cliente').value, ini: $('ini').value, fim: $('fim').value,
        robo: $('robo').value, competencia: $('competencia').value });
      $('log-montar').textContent = j.log || '';
      $('det-log').open = !j.params;
      if (j.escolherRobo) { status(st, 'Este cliente tem mais de um robô. Veja as opções no relatório e preencha o campo Robô.', 'erro'); $('det-log').open = true; return; }
      if (!j.params) { status(st, 'O montar.py parou (código ' + j.codigo + '). Veja o relatório abaixo.', 'erro'); return; }
      trabalho = j.id; params = j.params;
      preencherRevisao();
      status(st, 'Dados carregados.', 'ok');
      $('passo2').classList.remove('inativo');
      $('passo2').scrollIntoView({ behavior: 'smooth' });
    } catch (e) { status(st, e.message, 'erro'); }
    finally { $('btn-buscar').disabled = false; }
  });

  // ---------------------------------------------------------------- passo 2
  function itens(chave, lado){ var b = params[chave][lado]; return (b && b[0] && b[0].itens) || []; }
  function setItens(chave, lado, lista){
    var b = params[chave][lado];
    if (!b || !b[0]) params[chave][lado] = b = [{ topico: '', itens: [] }];
    var t = b[0].topico || '';
    if (!t || /REVISAR/.test(t)) b[0].topico = TOPICOS[chave][lado === 'esquerda' ? 0 : 1];
    b[0].itens = lista;
  }

  function preencherRevisao(){
    var g = params.grafico_execucoes || {}, v = params.valor_gerado || {}, d = params.disponibilidade || {};
    var vol = g.series ? g.series.reduce(function(s,x){ return s + x.valores.reduce(function(a,b){return a+b;},0); },0)
                       : (g.execucoes || []).reduce(function(a,b){ return a+b; }, 0);
    var sla = params.grafico_sla || {}, tc = (sla.chamados||[]).reduce(function(a,b){return a+b;},0),
        td = (sla.dentro_do_sla||[]).reduce(function(a,b){return a+b;},0);
    $('resumo').innerHTML = '';
    [[fmt(vol), 'itens processados'], [fmt(v.itens_entregues), 'itens entregues (sucesso)'],
     // mesma régua do slide: uma casa, arredondada para baixo
     [g.assertividade != null ? String(Math.floor(g.assertividade*10)/10).replace('.', ',') + '%' : '—', 'assertividade'],
     [td + ' de ' + tc, 'chamados no SLA'],
     [d.percentual != null ? String(Math.floor(d.percentual*10)/10).replace('.', ',') + '%' : 'a confirmar', 'disponibilidade']
    ].forEach(function(c){
      var el = document.createElement('div'); el.className = 'cartao';
      var b = document.createElement('b'); b.textContent = c[0];
      var s = document.createElement('span'); s.textContent = c[1];
      el.appendChild(b); el.appendChild(s); $('resumo').appendChild(el);
    });

    $('escopo').value = params.escopo || '';
    $('minutos').value = v.minutos_por_item != null ? v.minutos_por_item : '';
    $('custo').value = v.custo_hora != null ? v.custo_hora : '';
    $('origem').value = v.origem || '';
    $('entregas').value = (v.entregas || []).join('\\n');
    var pv = params.prevencao || null;
    $('bloco-prev').style.display = pv ? '' : 'none';
    if (pv) {
      for (var i = 0; i < 3; i++) {
        var dd = pv.destaques[i];
        $('dest' + i).value = dd ? dd.texto : '';
        $('lbl-dest' + i).textContent = dd ? ('Destaque ' + (i+1) + ' — ' + dd.numero + ' ' + dd.titulo) : 'Destaque ' + (i+1);
        $('dest' + i).disabled = !dd;
      }
      $('faixa').value = (pv.faixa && pv.faixa.texto) || '';
    }
    $('mel-esq').value = itens('melhorias', 'esquerda').join('\\n');
    $('mel-dir').value = itens('melhorias', 'direita').join('\\n');
    $('prox-esq').value = itens('proximas_evolucoes', 'esquerda').join('\\n');
    $('prox-dir').value = itens('proximas_evolucoes', 'direita').join('\\n');
    var oc = params.ocultar || [];
    ['valor','volume','prevencao'].forEach(function(k){ $('oc-' + k).checked = oc.indexOf(k) >= 0; });
    $('json').value = JSON.stringify(params, null, 2);
    marcarRevisar();
  }

  function lerRevisao(){
    params.escopo = $('escopo').value.trim();
    var v = params.valor_gerado = params.valor_gerado || {};
    v.minutos_por_item = $('minutos').value === '' ? null : Number($('minutos').value);
    v.custo_hora = $('custo').value === '' ? null : Number($('custo').value);
    if ($('origem').value) v.origem = $('origem').value; else delete v.origem;
    v.entregas = linhas($('entregas').value);
    if (params.prevencao) {
      params.prevencao.destaques.forEach(function(dd, i){ if (i < 3) dd.texto = $('dest' + i).value.trim(); });
      params.prevencao.faixa = params.prevencao.faixa || { titulo: '**Operação** protegida' };
      params.prevencao.faixa.texto = $('faixa').value.trim();
    }
    setItens('melhorias', 'esquerda', linhas($('mel-esq').value));
    setItens('melhorias', 'direita', linhas($('mel-dir').value));
    setItens('proximas_evolucoes', 'esquerda', linhas($('prox-esq').value));
    setItens('proximas_evolucoes', 'direita', linhas($('prox-dir').value));
    params.ocultar = ['valor','volume','prevencao'].filter(function(k){ return $('oc-' + k).checked; });
    if (!params.ocultar.length) delete params.ocultar;
    $('json').value = JSON.stringify(params, null, 2);
  }

  function marcarRevisar(){
    var campos = document.querySelectorAll('#passo2 textarea:not(#json), #passo2 input');
    campos.forEach(function(c){ c.classList.toggle('revisar', /REVISAR/.test(c.value)); });
    $('escopo-conta').textContent = $('escopo').value.replace(/\\*\\*/g, '').length + ' / ~200 caracteres';
    var n = (JSON.stringify(params).match(/REVISAR/g) || []).length;
    $('rev-pill').textContent = n ? (n + ' REVISAR pendente' + (n > 1 ? 's' : '')) : 'nada pendente';
    $('rev-pill').className = 'pill ' + (n ? 'alerta' : 'ok');
    $('btn-gerar').disabled = n > 0;
  }

  $('passo2').addEventListener('input', function(ev){
    if (ev.target.id === 'json') return;
    lerRevisao(); marcarRevisar();
  });
  $('btn-json').addEventListener('click', function(){
    try { params = JSON.parse($('json').value); preencherRevisao(); status($('st-gerar'), 'JSON aplicado.', 'ok'); }
    catch (e) { status($('st-gerar'), 'JSON inválido: ' + e.message, 'erro'); }
  });

  // ---------------------------------------------------------------- passo 3
  $('btn-gerar').addEventListener('click', async function(){
    var st = $('st-gerar'); this.disabled = true;
    lerRevisao();
    status(st, 'Gerando o .pptx e a conferência visual…');
    try {
      await chamar('PUT', BASE + '/trabalhos/' + trabalho + '/params', { params: params });
      var j = await chamar('POST', BASE + '/trabalhos/' + trabalho + '/gerar');
      $('log-gerar').textContent = j.log || '';
      if (!j.arquivo) { status(st, 'O gerar.py falhou. Veja o relatório.', 'erro'); $('det-gerar').open = true; return; }
      status(st, 'Pronto: ' + j.arquivo + ' (' + j.slides.length + ' slides).', 'ok');
      $('download').href = BASE + '/trabalhos/' + trabalho + '/download';
      $('download').textContent = '⬇ Baixar ' + j.arquivo;
      var box = $('slides'); box.innerHTML = '';
      j.slides.forEach(function(nome, i){
        var f = document.createElement('figure'); f.style.margin = '0';
        var img = document.createElement('img');
        img.src = BASE + '/trabalhos/' + trabalho + '/slides/' + encodeURIComponent(nome) + '?t=' + Date.now();
        img.alt = 'Slide ' + (i + 1);
        var cap = document.createElement('figcaption'); cap.textContent = 'Slide ' + (i + 1);
        f.appendChild(img); f.appendChild(cap); box.appendChild(f);
      });
      $('passo3').classList.remove('inativo');
      $('passo3').scrollIntoView({ behavior: 'smooth' });
    } catch (e) { status(st, e.message, 'erro'); }
    finally { marcarRevisar(); }
  });
})();
`;

function campo(id, rotulo, tipo, ajuda, extra) {
    const ctrl = tipo === 'area'
        ? `<textarea id="${id}" ${extra || ''}></textarea>`
        : `<input id="${id}" type="${tipo}" ${extra || ''}>`;
    return `<div class="campo"><label id="lbl-${id}" for="${id}">${rotulo}</label>${ctrl}${ajuda ? `<div class="ajuda">${ajuda}</div>` : ''}</div>`;
}

function paginaGerador(opts) {
    const embed = !!(opts && opts.embed);
    const sufixo = embedQuerySuffix(embed);
    return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gerador de ATE - Yank Solutions</title>
<style>${STYLES}</style>
</head>
<body class="${embed ? 'embed' : ''}">
<div class="header-nav">
  <a class="home-button" href="/${sufixo}">&larr; Menu Principal</a>
  <a class="home-button" href="/gerador-ate${sufixo}">📑 Gerador de ATE</a>
</div>
<div class="container">
  <h1>Gerador de <span>ATE</span></h1>
  <p class="sub">Acompanhamento Tático/Estratégico no modelo oficial. Banco e GLPI são consultados só em leitura; o escopo e o segmento saem do vault.</p>

  <section class="passo" id="passo1">
    <h2><span class="num">1</span> Cliente e trimestre</h2>
    <form id="form-buscar">
      <div class="grade">
        ${campo('cliente', 'Cliente (como na planilha)', 'text', '', 'required maxlength="80" placeholder="Nome do cliente"')}
        ${campo('ini', '1º mês', 'month', '', 'required')}
        ${campo('fim', '3º mês', 'month', '', 'required')}
        ${campo('robo', 'Robô (opcional)', 'text', 'só se o cliente tiver mais de um', 'maxlength="44" placeholder="ABC01 ou nº da linha"')}
        ${campo('competencia', 'Competência (opcional)', 'text', 'padrão: o 3º mês', 'maxlength="6" placeholder="Jun/26"')}
      </div>
      <div class="acoes"><button id="btn-buscar" type="submit">Buscar dados</button><span class="status" id="st-buscar"></span></div>
      <details id="det-log"><summary>Relatório do montar.py (o que conferir antes de gerar)</summary><pre id="log-montar"></pre></details>
    </form>
  </section>

  <section class="passo inativo" id="passo2">
    <h2><span class="num">2</span> Revisar os textos <span class="pill alerta" id="rev-pill">—</span></h2>
    <div class="resumo" id="resumo"></div>

    <div class="campo"><label for="escopo">Escopo (slide 2) — da nota do robô no vault; condensar, sem inventar</label>
      <textarea id="escopo"></textarea><div class="ajuda" id="escopo-conta"></div></div>

    <div class="grade">
      ${campo('minutos', 'Tempo manual por item (min)', 'number', 'do cliente; vazio = "a confirmar"', 'min="0" step="0.1"')}
      ${campo('custo', 'Custo/hora da equipe (R$)', 'number', 'do cliente; vazio = "a confirmar"', 'min="0" step="1"')}
      <div class="campo"><label for="origem">Origem desses valores</label>
        <select id="origem"><option value="">informados pelo cliente</option><option value="estimados pela equipe Yank">estimados pela equipe Yank</option></select></div>
    </div>
    ${campo('entregas', 'O que foi entregue no trimestre (slide 2) — uma linha por item', 'area', '**negrito** no número')}

    <div id="bloco-prev">
      <div class="grade dois">
        ${campo('dest0', 'Destaque 1', 'area', '', 'rows="2"')}
        ${campo('dest1', 'Destaque 2', 'area', '', 'rows="2"')}
        ${campo('dest2', 'Destaque 3', 'area', '', 'rows="2"')}
        ${campo('faixa', 'Faixa do slide 6 — o que a equipe fez para evitar falhas', 'area', '', 'rows="2"')}
      </div>
    </div>

    <div class="grade dois">
      ${campo('mel-esq', 'Slide 7 · O que foi entregue no robô (uma por linha)', 'area')}
      ${campo('mel-dir', 'Slide 7 · O que fizemos para evitar falhas', 'area')}
      ${campo('prox-esq', 'Slide 8 · Próximas evoluções', 'area')}
      ${campo('prox-dir', 'Slide 8 · Oportunidades no segmento (do vault, sem nome de cliente)', 'area')}
    </div>

    <div class="campo"><label>Tirar slide opcional mesmo com dado</label>
      <div class="check">
        <label><input type="checkbox" id="oc-valor"> 3 · Horas e Valor Financeiro</label>
        <label><input type="checkbox" id="oc-volume"> 5 · Volume Processado</label>
        <label><input type="checkbox" id="oc-prevencao"> 6 · Evitar falhas</label>
      </div></div>

    <details><summary>params.json completo (avançado)</summary>
      <textarea id="json" style="min-height:280px;font-family:Consolas,monospace;font-size:12px"></textarea>
      <div class="acoes"><button class="secundario" type="button" id="btn-json">Aplicar JSON</button></div>
    </details>

    <div class="acoes"><button id="btn-gerar" type="button" disabled>Gerar apresentação</button><span class="status" id="st-gerar"></span></div>
  </section>

  <section class="passo inativo" id="passo3">
    <h2><span class="num">3</span> Conferir e baixar</h2>
    <a class="home-button" style="background:var(--azul)" id="download" href="#">⬇ Baixar</a>
    <div class="slides" id="slides"></div>
    <details id="det-gerar"><summary>Relatório do gerar.py</summary><pre id="log-gerar"></pre></details>
  </section>
</div>
${getGlobalScripts()}
<script>${SCRIPT}</script>
</body>
</html>`;
}

module.exports = { paginaGerador };
