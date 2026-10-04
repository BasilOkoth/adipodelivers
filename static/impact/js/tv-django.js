const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stage=document.getElementById('stage');
let slides=[],nodes=[],i=0,timer,dataCache=null;
const trim=(s,n=165)=>{s=String(s||'').trim();return s.length>n?s.slice(0,n-1).trim()+'…':s};
function clock(){const el=document.getElementById('clock');if(el)el.textContent=new Date().toLocaleTimeString('en-KE',{hour:'2-digit',minute:'2-digit'})}
clock();setInterval(clock,1000);
function initials(name){return String(name||'').replace(/\b(Hon|Dr|Mr|Mrs|Ms|Prof)\.?\b/gi,'').trim().split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'IP'}
function lang(){return dataCache?.language?.mode||window.TV_LANGUAGE_MODE||'en'}
function pick(en,local){if(lang()==='local')return local||en||'';return en||local||''}
function bi(en,local,tag='div',max=180){en=trim(en,max);local=trim(local,max);if(lang()==='bilingual'&&local&&local!==en)return `<${tag} class="bilingual-copy"><span>${esc(en||'')}</span><small>${esc(local)}</small></${tag}>`;return `<${tag}>${esc(trim(pick(en,local),max))}</${tag}>`}
function wardLabel(p){return pick(p.ward,p.ward_local)}
function locationLabel(p){return pick(p.location,p.location_local)}
function localModeQuery(){return `?lang=${encodeURIComponent(lang())}`}
function statusBadge(p,b){return b.tv_show_project_status?`<div class="video-badge"><span>PROJECT STATUS</span><b>${esc(p.verification_label)}</b></div>`:''}

function videoSlide(p,m,b){
  const title=bi(p.short_title,p.short_title_local,'h2',95);
  const caption=bi(m.caption||p.summary,m.caption_local||p.summary_local,'p',120);
  const loc=pick(m.location||p.location,m.location_local||p.location_local);
  const ward=pick(m.ward||p.ward,m.ward_local||p.ward_local);
  return {
    duration:Math.max(9000,(m.end||m.duration||15)*1000),
    html:`<section class="slide video-slide">
      <video muted playsinline preload="auto" ${m.poster?`poster="${esc(m.poster)}"`:''}><source src="${esc(m.url)}" type="video/mp4"></video>
      <div class="video-copy">
        <div class="eyebrow">${esc(p.sector)} · ${esc(ward)}</div>
        ${title}
        ${caption}
        <div class="clip-route">PROJECT SITE · ${esc(trim(locationLabel(p),140))}</div>
      </div>
      ${statusBadge(p,b)}
    </section>`
  }
}

function imageSlide(p,m,b){
  const title=bi(p.short_title,p.short_title_local,'h2',95);
  const caption=bi(m.caption||p.summary,m.caption_local||p.summary_local,'p',110);
  const loc=pick(m.location||p.location,m.location_local||p.location_local);
  const ward=wardLabel(p);
  const constituency=b.jurisdiction||'';
  return {
    duration:Math.max(9000,(m.duration||12)*1000),
    html:`<section class="slide image-slide">
      <img class="story-image" src="${esc(m.url)}" alt="${esc(m.title||p.short_title)}" onerror="this.classList.add('media-error')">
      <div class="image-shade"></div>
      <div class="video-copy photo-copy">
        <div class="eyebrow">${esc(p.sector)} · ${esc(ward)}</div>
        ${title}
        ${caption}
        <ul class="story-bullets">
          <li><span>Project site</span><b>${esc(trim(loc,90))}</b></li>
          <li><span>Ward</span><b>${esc(ward)}</b></li>
          <li><span>Constituency</span><b>${esc(constituency)}</b></li>
        </ul>
      </div>
      ${statusBadge(p,b)}
    </section>`
  }
}

function build(data){
  dataCache=data;
  const b=data.brand||{}, domain=b.domain||location.host;
  const jurisdiction=[b.jurisdiction,b.county].filter(Boolean).join(' · ');
  const introKicker=b.tv_intro_kicker||jurisdiction||'PUBLIC IMPACT CHANNEL';
  const photo=b.tv_show_leader_photo
    ? `<div class="mp-photo-wrap"><img class="mp-photo" src="${esc(b.leader_photo||'')}" alt="${esc(b.leader||b.name)}" onerror="this.parentElement.classList.add('fallback')"><div class="mp-photo-fallback">${esc(initials(b.leader))}</div><div class="mp-photo-shade"></div></div>`
    : `<div class="mp-initials">${esc(initials(b.leader))}</div>`;

  slides=[{
    duration:Math.max(6000,(b.tv_intro_duration_seconds||8)*1000),
    html:`<section class="slide hero-slide active">
      <div class="grid-bg"></div>
      <div>
        <div class="eyebrow">${esc(introKicker)}</div>
        <h1>${esc(b.tv_intro_headline||'Impact you can see.')}</h1>
        <p>${esc(trim(b.tv_intro_subheadline||b.tagline||'Projects, places and evidence from across the constituency.',190))}</p>
        <div class="hero-line"><span>PROJECTS</span><span>PEOPLE</span><span>PLACES</span><span>EVIDENCE</span></div>
      </div>
      <div class="mp-panel">
        ${photo}
        <div class="mp-meta"><small>${esc((b.leader_title||'PUBLIC OFFICE').toUpperCase())}</small><b>${esc(b.leader||b.name)}</b><span>${esc(b.jurisdiction||'')}</span></div>
      </div>
    </section>`
  }];

  (data.projects||[]).forEach(p=>{
    (p.media||[]).filter(m=>m.type==='video'&&m.url).forEach(m=>slides.push(videoSlide(p,m,b)));
    (p.media||[]).filter(m=>m.type==='image'&&m.url).forEach(m=>slides.push(imageSlide(p,m,b)));

    const title=bi(p.short_title,p.short_title_local,'h2',105);
    const summary=bi(p.summary,p.summary_local,'p',150);
    slides.push({duration:9000,html:`<section class="slide record-slide"><div class="record-layout"><div><div class="eyebrow">${esc(p.sector)} · ${esc(wardLabel(p))}</div>${title}${summary}<div class="route-chip">📍 ${esc(trim(locationLabel(p),145))}</div>${b.tv_show_website?`<a class="open-record" href="${esc(p.url+localModeQuery())}">READ MORE AT ${esc(domain)} →</a>`:''}</div><div class="record-facts"><div class="record-fact"><span>AREA</span><b>${esc(wardLabel(p))}</b></div><div class="record-fact"><span>WHAT WAS DONE</span><b>${esc(trim(pick(p.intervention,p.intervention_local)||p.sector,90))}</b></div><div class="record-fact"><span>PROJECT RECORD</span><b>${esc(p.id)}</b></div></div></div></section>`});

    if(p.impacts?.length){
      const cards=p.impacts.slice(0,3).map((x,n)=>{
        const local=x.local||'';
        const content=lang()==='bilingual'&&local?`<span>${esc(trim(x.en,105))}</span><small>${esc(trim(local,105))}</small>`:`<span>${esc(trim(pick(x.en,local),105))}</span>`;
        return `<div class="metric"><strong>0${n+1}</strong>${content}</div>`
      }).join('');
      slides.push({duration:9000,html:`<section class="slide impact-slide"><div class="eyebrow">IMPACT · ${esc(wardLabel(p))}</div><h2>How this project is improving lives.</h2><div class="metrics">${cards}</div></section>`})
    }
  });

  const wards=(data.wards||[]);
  slides.push({duration:9000,html:`<section class="slide wards-slide"><div class="eyebrow">GEOGRAPHIC COVERAGE</div><h2>Impact across the constituency.</h2><div class="wards">${wards.map(w=>{const wn=pick(w.en,w.local);const count=(data.projects||[]).filter(p=>p.ward===w.en).length;return `<div class="ward">${esc(wn)}<span>${count} published project record${count===1?'':'s'}</span></div>`}).join('')}</div></section>`});

  slides.push({duration:9000,html:`<section class="slide closing-slide"><div class="eyebrow">PUBLIC ACCOUNTABILITY</div><h2>The screen shows the impact.<br>The website carries the full record.</h2><p>Projects · locations · photos · videos · maps · supporting documents</p>${b.tv_show_qr||b.tv_show_website?`<div class="closing-domain">${b.tv_show_qr?`<img src="/qr/" alt="QR">`:''}${b.tv_show_website?`<div><small>SCAN OR VISIT</small><b>${esc(domain)}</b></div>`:''}</div>`:''}<div class="disclaimer">PUBLIC PROJECT RECORDS · DETAILS MAY INCLUDE PHOTOGRAPHS, VIDEO, LOCATIONS AND SUPPORTING EVIDENCE.</div></section>`});

  stage.innerHTML=slides.map((s,idx)=>`<div class="slide-wrap" data-index="${idx}">${s.html}</div>`).join('');
  nodes=[...stage.querySelectorAll('.slide')];
  i=0;
  activate(0);
}

function activate(index){
  if(!nodes.length)return;
  nodes.forEach((n,idx)=>{
    const active=idx===index;
    n.classList.toggle('active',active);
    const vid=n.querySelector('video');
    if(vid){if(active){vid.currentTime=0;vid.play().catch(()=>{})}else{vid.pause()}}
  });
  const slideNo=document.getElementById('slideNo');
  if(slideNo)slideNo.textContent=`${index+1} / ${nodes.length}`;
  const bar=document.getElementById('progressBar');
  if(bar){bar.style.transition='none';bar.style.width='0%';requestAnimationFrame(()=>requestAnimationFrame(()=>{bar.style.transition=`width ${slides[index].duration}ms linear`;bar.style.width='100%'}))}
  clearTimeout(timer);
  timer=setTimeout(()=>{i=(i+1)%nodes.length;activate(i)},slides[index].duration)
}

fetch(window.TV_PLAYLIST_URL)
  .then(r=>r.json())
  .then(build)
  .catch(e=>{stage.innerHTML='<div class="loading">Unable to load the TV playlist.</div>';console.error(e)});

document.addEventListener('keydown',e=>{
  if(!nodes.length)return;
  if(e.key==='ArrowRight'){i=(i+1)%nodes.length;activate(i)}
  if(e.key==='ArrowLeft'){i=(i-1+nodes.length)%nodes.length;activate(i)}
  if(e.key.toLowerCase()==='f'){document.documentElement.requestFullscreen?.()}
});
