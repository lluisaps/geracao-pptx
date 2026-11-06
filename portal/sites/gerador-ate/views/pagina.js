const { embedQuerySuffix } = require('../../../config/embedMode');
const { getGlobalScripts } = require('../../../core/globalScripts');

const STYLES = `
:root{--azul:#0BBBEF;--escuro:#0b1720;--borda:#d9e2e8;--texto:#1d2a33;--suave:#5d6d78;--fundo:#f3f6f8}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:var(--fundo);color:var(--texto);display:flex;flex-direction:column}
.header-nav{display:flex;justify-content:space-between;align-items:center;padding:10px 20px;background:var(--escuro);flex:none}
.home-button{color:#fff;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:8px;background:rgba(255,255,255,.08);border:0;cursor:pointer;font-family:inherit}
.home-button:hover{background:rgba(255,255,255,.16)}
body.embed .header-nav{display:none}
.app{flex:1;display:grid;grid-template-columns:minmax(0,1fr) 380px;min-height:0}
.chat{display:flex;flex-direction:column;min-height:0;border-right:1px solid var(--borda)}
.mensagens{flex:1;overflow-y:auto;padding:24px 24px 8px}
.msg{max-width:780px;margin:0 auto 14px;display:flex;gap:10px}
.msg .av{flex:none;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px}
.msg.agente .av{background:var(--escuro);color:var(--azul);font-weight:700}
.msg.voce{flex-direction:row-reverse}
.msg.voce .av{background:var(--azul);color:#fff}
.balao{background:#fff;border:1px solid var(--borda);border-radius:12px;padding:10px 14px;font-size:14.5px;line-height:1.55;min-width:0;overflow-wrap:anywhere}
.msg.voce .balao{background:#e6f7fd;border-color:#bfe9f7;white-space:pre-wrap}
.balao p{margin:0 0 8px}.balao p:last-child{margin-bottom:0}
.balao ul,.balao ol{margin:4px 0 8px;padding-left:20px}
.balao code{background:#eef3f6;padding:1px 5px;border-radius:4px;font-size:13px}
.balao table{border-collapse:collapse;margin:6px 0;font-size:13px}
.balao td,.balao th{border:1px solid var(--borda);padding:4px 8px;text-align:right}
.balao td:first-child,.balao th:first-child{text-align:left}
.balao h3,.balao h4{margin:10px 0 4px;font-size:14.5px}
.ferramenta{font-size:12.5px;color:var(--suave);margin:4px 0}
.digitando{color:var(--suave);font-size:13px}
.boasvindas{max-width:780px;margin:30px auto;text-align:center;color:var(--suave)}
.boasvindas h1{color:var(--texto);font-size:24px;margin:0 0 6px}.boasvindas h1 span{color:var(--azul)}
.sugestoes{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:16px}
.sugestoes button{background:#fff;border:1px solid var(--borda);border-radius:999px;padding:7px 14px;font-size:13px;color:var(--texto);cursor:pointer;font-family:inherit}
.sugestoes button:hover{border-color:var(--azul)}
.entrada{flex:none;padding:12px 24px 18px}
.caixa{max-width:780px;margin:0 auto;display:flex;gap:8px;background:#fff;border:1px solid var(--borda);border-radius:14px;padding:8px}
.caixa textarea{flex:1;border:0;resize:none;font:inherit;font-size:14.5px;padding:6px 8px;max-height:180px;outline:none;color:var(--texto);background:transparent}
.caixa button{background:var(--azul);color:#fff;border:0;border-radius:10px;padding:0 18px;font-weight:600;cursor:pointer;font-family:inherit}
.caixa button[disabled]{background:#9fb3bf;cursor:not-allowed}
.nota{max-width:780px;margin:6px auto 0;font-size:11.5px;color:var(--suave);text-align:center}
.painel{overflow-y:auto;padding:20px;background:#fff}
.painel h2{font-size:15px;margin:0 0 4px}
.painel .vazio{color:var(--suave);font-size:13px;line-height:1.5}
.baixar{display:inline-block;margin:10px 0 14px;background:var(--azul);color:#fff;text-decoration:none;padding:9px 14px;border-radius:8px;font-weight:600;font-size:14px}
.slides figure{margin:0 0 12px}
.slides img{width:100%;border-radius:8px;border:1px solid var(--borda);display:block;cursor:zoom-in}
.slides figcaption{font-size:12px;color:var(--suave);margin-top:3px}
.zoom{position:fixed;inset:0;background:rgba(10,20,28,.85);display:none;align-items:center;justify-content:center;z-index:50;padding:24px}
.zoom img{max-width:100%;max-height:100%;border-radius:8px}
@media (max-width:900px){.app{grid-template-columns:1fr}.painel{border-top:1px solid var(--borda)}.chat{border-right:0}}
`;

const SCRIPT = `
(function(){
  var BASE = '/gerador-ate/api';
  var $ = function(id){ return document.getElementById(id); };
  var conversa = null, ocupado = false;

  function esc(t){ return t.replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function inline(t){
    return esc(t).replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>').replace(/\`([^\`]+)\`/g, '<code>$1</code>');
  }
  // markdown enxuto: parágrafos, listas, tabelas, títulos, negrito, código
  function md(texto){
    var linhas = texto.split('\\n'), html = '', lista = null, tabela = null;
    function fecha(){ if (lista){ html += '</' + lista + '>'; lista = null; } if (tabela){ html += '</table>'; tabela = null; } }
    linhas.forEach(function(l){
      var t = l.trim();
      if (/^\\|.*\\|$/.test(t)) {
        if (/^\\|[\\s:|-]+\\|$/.test(t)) return;
        if (lista){ html += '</' + lista + '>'; lista = null; }
        var cel = t.slice(1, -1).split('|').map(function(c){ return inline(c.trim()); });
        if (!tabela){ tabela = true; html += '<table><tr><th>' + cel.join('</th><th>') + '</th></tr>'; }
        else html += '<tr><td>' + cel.join('</td><td>') + '</td></tr>';
        return;
      }
      var m;
      if ((m = t.match(/^[-*]\\s+(.*)/))) { if (tabela){ html += '</table>'; tabela = null; } if (lista !== 'ul'){ fecha(); html += '<ul>'; lista = 'ul'; } html += '<li>' + inline(m[1]) + '</li>'; return; }
      if ((m = t.match(/^\\d+[.)]\\s+(.*)/))) { if (tabela){ html += '</table>'; tabela = null; } if (lista !== 'ol'){ fecha(); html += '<ol>'; lista = 'ol'; } html += '<li>' + inline(m[1]) + '</li>'; return; }
      fecha();
      if (!t) return;
      if ((m = t.match(/^#{1,4}\\s+(.*)/))) { html += '<h4>' + inline(m[1]) + '</h4>'; return; }
      html += '<p>' + inline(t) + '</p>';
    });
    fecha();
    return html;
  }

  function rolar(){ var m = $('mensagens'); m.scrollTop = m.scrollHeight; }
  function bolha(quem){
    var bv = $('boasvindas'); if (bv) bv.remove();
    var d = document.createElement('div'); d.className = 'msg ' + quem;
    var av = document.createElement('div'); av.className = 'av'; av.textContent = quem === 'voce' ? 'Eu' : 'Y';
    var b = document.createElement('div'); b.className = 'balao';
    d.appendChild(av); d.appendChild(b); $('mensagens').appendChild(d); rolar();
    return b;
  }

  function mostrarSlides(ev){
    if (!ev.arquivo) return;
    $('painel-vazio').style.display = 'none';
    var a = $('baixar'); a.style.display = 'inline-block';
    a.href = BASE + '/conversas/' + conversa + '/download?v=' + ev.versao;
    a.textContent = '⬇ Baixar ' + ev.arquivo;
    $('painel-sub').textContent = ev.slides.length + ' slides';
    var box = $('slides'); box.innerHTML = '';
    ev.slides.forEach(function(nome, i){
      var f = document.createElement('figure');
      var img = document.createElement('img');
      img.src = BASE + '/conversas/' + conversa + '/slides/' + encodeURIComponent(nome) + '?v=' + ev.versao;
      img.alt = 'Slide ' + (i + 1);
      img.onclick = function(){ $('zoom-img').src = img.src; $('zoom').style.display = 'flex'; };
      var c = document.createElement('figcaption'); c.textContent = 'Slide ' + (i + 1);
      f.appendChild(img); f.appendChild(c); box.appendChild(f);
    });
  }

  async function garantirConversa(){
    if (conversa) return;
    var r = await fetch(BASE + '/conversas', { method: 'POST', credentials: 'same-origin' });
    var j = await r.json();
    if (!r.ok) throw new Error(j.erro || 'não consegui abrir a conversa');
    conversa = j.id;
  }

  async function enviar(texto){
    texto = texto.trim(); if (!texto || ocupado) return;
    ocupado = true; $('enviar').disabled = true; $('texto').value = ''; ajustar();
    bolha('voce').textContent = texto;
    var b = bolha('agente');
    var corpo = '', ferr = document.createElement('div');
    b.innerHTML = '<div class="digitando">pensando…</div>';
    try {
      await garantirConversa();
      var r = await fetch(BASE + '/conversas/' + conversa + '/mensagens', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texto: texto }) });
      if (!r.ok || !r.body) { var j = await r.json().catch(function(){ return {}; }); throw new Error(j.erro || ('HTTP ' + r.status)); }
      var leitor = r.body.getReader(), dec = new TextDecoder(), resto = '';
      var desenhar = function(status){
        b.innerHTML = '';
        if (ferr.childNodes.length) b.appendChild(ferr);
        var c = document.createElement('div'); c.innerHTML = md(corpo); b.appendChild(c);
        if (status) { var s = document.createElement('div'); s.className = 'digitando'; s.textContent = status; b.appendChild(s); }
        rolar();
      };
      while (true) {
        var p = await leitor.read(); if (p.done) break;
        resto += dec.decode(p.value, { stream: true });
        var linhas = resto.split('\\n'); resto = linhas.pop();
        linhas.forEach(function(l){
          if (!l.trim()) return;
          var ev = JSON.parse(l);
          if (ev.tipo === 'texto') { corpo += ev.texto; desenhar('…'); }
          else if (ev.tipo === 'ferramenta') { var f = document.createElement('div'); f.className = 'ferramenta'; f.textContent = ev.rotulo; ferr.appendChild(f); desenhar(ev.rotulo); }
          else if (ev.tipo === 'slides') mostrarSlides(ev);
          else if (ev.tipo === 'erro') { corpo += '\\n\\n**Erro:** ' + ev.erro; }
        });
      }
      desenhar('');
    } catch (e) {
      corpo += '\\n\\n**Erro:** ' + e.message; b.innerHTML = md(corpo);
    } finally {
      ocupado = false; $('enviar').disabled = false; $('texto').focus();
    }
  }

  function ajustar(){ var t = $('texto'); t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight, 180) + 'px'; }
  $('texto').addEventListener('input', ajustar);
  $('texto').addEventListener('keydown', function(e){ if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(this.value); } });
  $('enviar').addEventListener('click', function(){ enviar($('texto').value); });
  document.querySelectorAll('.sugestoes button').forEach(function(btn){
    btn.addEventListener('click', function(){ $('texto').value = btn.dataset.texto; ajustar(); $('texto').focus(); });
  });
  $('nova').addEventListener('click', function(){ if (!ocupado) location.reload(); });
  $('zoom').addEventListener('click', function(){ this.style.display = 'none'; });
  window.geradorAte = { enviar: enviar };
})();
`;

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
  <button class="home-button" id="nova" type="button">＋ Nova conversa</button>
</div>
<div class="app">
  <section class="chat">
    <div class="mensagens" id="mensagens">
      <div class="boasvindas" id="boasvindas">
        <h1>Gerador de <span>ATE</span></h1>
        <p>Converse com o agente: diga o cliente e o trimestre, responda o que ele perguntar e peça ajustes.<br>
        Ele consulta planilha, banco e GLPI (só leitura) e o vault, e gera no modelo oficial.</p>
        <div class="sugestoes">
          <button type="button" data-texto="Preciso do ATE do cliente , trimestre 2026-04 a 2026-06.">Começar um ATE</button>
          <button type="button" data-texto="Quais slides o ATE tem e de onde sai cada número?">Como funciona o ATE?</button>
          <button type="button" data-texto="O que você precisa de mim para gerar um ATE completo?">O que você precisa de mim?</button>
        </div>
      </div>
    </div>
    <div class="entrada">
      <div class="caixa">
        <textarea id="texto" rows="1" placeholder="Escreva para o agente… (Enter envia, Shift+Enter quebra linha)"></textarea>
        <button id="enviar" type="button">Enviar</button>
      </div>
      <div class="nota">O agente pode errar: confira os números na conferência antes de mandar ao cliente.</div>
    </div>
  </section>
  <aside class="painel">
    <h2>Apresentação</h2>
    <div class="vazio" id="painel-sub"></div>
    <p class="vazio" id="painel-vazio">Quando o agente gerar o ATE, os slides aparecem aqui com o botão de baixar.</p>
    <a class="baixar" id="baixar" href="#" style="display:none">⬇ Baixar</a>
    <div class="slides" id="slides"></div>
  </aside>
</div>
<div class="zoom" id="zoom"><img id="zoom-img" alt="Slide ampliado"></div>
${getGlobalScripts()}
<script>${SCRIPT}</script>
</body>
</html>`;
}

module.exports = { paginaGerador };
