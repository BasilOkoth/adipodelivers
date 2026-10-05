const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stage=document.getElementById('stage');
let slides=[],nodes=[],i=0,timer,dataCache=null;

const trim=(s,n=165)=>{s=String(s||'').trim();return s.length>n?s.slice(0,n-1).trim()+'…':s};
const clean=s=>String(s||'').replace(/\s+/g,' ').trim();

function clock(){
  const el=document.getElementById('clock');
  if(el)el.textContent=new Date().toLocaleTimeString('en-KE',{hour:'2-digit',minute:'2-digit'});
}
clock();setInterval(clock,1000);

function initials(name){
  return String(name||'').replace(/\b(Hon|Dr|Mr|Mrs|Ms|Prof)\.?\b/gi,'').trim()
    .split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'AD';
}
function lang(){return dataCache?.language?.mode||window.TV_LANGUAGE_MODE||'en'}
function pick(en,local){if(lang()==='local')return local||en||'';return en||local||''}
function bi(en,local,tag='div',max=180){
  en=trim(en,max);local=trim(local,max);
  if(lang()==='bilingual'&&local&&local!==en){
    return `<${tag} class="bilingual-copy"><span>${esc(en||'')}</span><small>${esc(local)}</small></${tag}>`;
  }
  return `<${tag}>${esc(trim(pick(en,local),max))}</${tag}>`;
}
function wardLabel(p){return pick(p.ward,p.ward_local)}
function locationLabel(p){return pick(p.location,p.location_local)}
function localModeQuery(){return `?lang=${encodeURIComponent(lang())}`}
function money(v){
  const n=Number(v);
  if(!Number.isFinite(n)||n<=0)return '';
  return `KES ${new Intl.NumberFormat('en-KE',{maximumFractionDigits:0}).format(n)}`;
}
function dateLabel(v){
  if(!v)return '';
  const d=new Date(`${v}T00:00:00`);
  if(Number.isNaN(d.getTime()))return v;
  return d.toLocaleDateString('en-KE',{day:'numeric',month:'short',year:'numeric'});
}
function joinTicker(parts){return parts.map(clean).filter(Boolean).join('   •   ')}
function projectTicker(p,b,extra=''){
  const impacts=(p.impacts||[]).slice(0,2).map(x=>pick(x.en,x.local)).filter(Boolean);
  return joinTicker([
    p.short_title||p.title,
    `${p.sector||'Project'} — ${wardLabel(p)}`,
    locationLabel(p),
    p.intervention,
    p.budget?`Investment: ${money(p.budget)}`:'',
    p.funding_source?`Funding: ${p.funding_source}`:'',
    p.implementing_agency?`Implementing agency: ${p.implementing_agency}`:'',
    p.beneficiaries?`Beneficiaries: ${Number(p.beneficiaries).toLocaleString('en-KE')}`:'',
    p.completion_date?`Completion: ${dateLabel(p.completion_date)}`:(p.start_date?`Started: ${dateLabel(p.start_date)}`:''),
    impacts.length?`Impact: ${impacts.join(' / ')}`:'',
    extra,
    b.tv_show_website&&b.domain?`More: ${b.domain}`:''
  ]);
}

function videoSlide(p,m,b){
  const title=bi(p.short_title,p.short_title_local,'h2',84);
  const caption=bi(m.caption||p.summary,m.caption_local||p.summary_local,'p',115);
  const ward=pick(m.ward||p.ward,m.ward_local||p.ward_local);
  return {
    duration:Math.max(9000,(m.end||m.duration||15)*1000),
    ticker:projectTicker(p,b,m.caption||''),
    html:`<section class="slide clean-media-slide">
      <div class="media-copy">
        <div class="eyebrow">${esc(p.sector)} · ${esc(ward)}</div>
        ${title}${caption}
        <div class="clip-route">${esc(trim(locationLabel(p),135))}</div>
      </div>
      <div class="media-window">
        <video muted playsinline preload="auto" ${m.poster?`poster="${esc(m.poster)}"`:''}>
          <source src="${esc(m.url)}" type="video/mp4">
        </video>
        <div class="media-window-shade"></div>
      </div>
    </section>`
  };
}

function imageSlide(p,m,b){
  const loc=pick(m.location||p.location,m.location_local||p.location_local);
  const ward=wardLabel(p);
  const shortCaption=trim(m.caption||p.summary,100);
  return {
    duration:Math.max(9000,(m.duration||12)*1000),
    ticker:projectTicker(p,b,m.caption||''),
    html:`<section class="slide editorial-photo-slide">
      <img class="editorial-photo-image" src="${esc(m.url)}" alt="${esc(m.title||p.short_title)}">
      <div class="editorial-photo-vignette"></div>

      <div class="editorial-photo-top">
        <div class="editorial-sector">${esc(p.sector)}</div>
        <div class="editorial-ward">${esc(ward)}</div>
      </div>

      <div class="editorial-photo-story">
        <div class="editorial-accent"></div>
        <h2>${esc(trim(p.short_title||p.title,82))}</h2>
        ${shortCaption?`<p>${esc(shortCaption)}</p>`:''}
        <div class="editorial-location">
          <span>PROJECT SITE</span>
          <b>${esc(trim(loc,88))}</b>
        </div>
      </div>

      <div class="editorial-photo-index">
        <span>ADIPO DELIVERS</span>
        <b>PROJECT IMPACT</b>
      </div>
    </section>`
  };
}

function constituencyPulseSlide(data,b){
  const projects=data.projects||[];
  const wards=data.wards||[];
  const sectors=[...new Set(projects.map(p=>p.sector).filter(Boolean))];
  const activeWards=new Set(projects.map(p=>p.ward).filter(Boolean));
  const nodePositions=[['18%','24%'],['48%','13%'],['79%','24%'],['87%','54%'],['72%','82%'],['40%','87%'],['14%','68%'],['10%','43%']];
  const nodes=wards.slice(0,8).map((w,idx)=>{
    const name=pick(w.en,w.local),count=projects.filter(p=>p.ward===w.en).length,pos=nodePositions[idx%nodePositions.length];
    return `<div class="ward-node ${count?'live-node':''}" style="--x:${pos[0]};--y:${pos[1]}"><b>${esc(name)}</b><span>${count?`${count} project${count===1?'':'s'} active in record`:'No published project yet'}</span></div>`;
  }).join('');
  const feed=projects.slice(0,4).map(p=>`<div class="feed-item"><small>${esc(p.sector||'PROJECT')}</small><b>${esc(trim(p.short_title,55))}</b><span>${esc(wardLabel(p))}</span></div>`).join('');
  const activeDetails=projects.slice(0,4).map(p=>`${p.short_title||p.title} — ${wardLabel(p)}`);
  return {
    duration:11000,
    ticker:joinTicker([`${projects.length} published project records`,`${activeWards.size} wards represented`,`${sectors.length} sectors`,...activeDetails,b.domain?`Explore: ${b.domain}`:'']),
    html:`<section class="slide pulse-slide">
      <div class="pulse-head"><div class="pulse-title"><div class="eyebrow">LIVE CONSTITUENCY VIEW</div><h2>Where impact is happening now.</h2></div>
      <div class="pulse-kpis"><div class="pulse-kpi"><strong>${projects.length}</strong><span>Project records</span></div><div class="pulse-kpi"><strong>${activeWards.size}</strong><span>Wards with projects</span></div><div class="pulse-kpi"><strong>${sectors.length}</strong><span>Sectors</span></div></div></div>
      <div class="pulse-body"><div class="pulse-map"><div class="pulse-orbit"></div><div class="pulse-orbit two"></div><div class="pulse-hub"><div><b>KARACHUONYO</b><span>IMPACT PULSE</span></div></div>${nodes}</div>
      <div class="pulse-feed"><h3>LIVE PROJECT FEED</h3><div class="feed-list">${feed||'<div class="feed-empty">Published project records will appear here as they are added.</div>'}</div></div></div>
    </section>`
  };
}

function build(data){
  dataCache=data;
  const b=data.brand||{},domain=b.domain||location.host,jurisdiction=b.jurisdiction||'Karachuonyo Constituency';
  let portrait='';
  if(b.tv_show_leader_photo&&b.leader_photo){
    portrait=`<div class="mp-photo-stage"><img class="mp-photo" src="${esc(b.leader_photo)}" alt="${esc(b.leader||'Member of Parliament')}" onerror="this.parentElement.classList.add('fallback')"><div class="mp-photo-fallback">${esc(initials(b.leader))}</div></div>`;
  }else{portrait=`<div class="mp-photo-stage"><div class="mp-initials">${esc(initials(b.leader))}</div></div>`;}

  slides=[{
    duration:Math.max(7000,(b.tv_intro_duration_seconds||9)*1000),
    ticker:joinTicker([b.tv_ticker_text||'Karachuonyo development impact',`${(data.projects||[]).length} project records`,jurisdiction,b.tv_show_website&&domain?`Explore the full record: ${domain}`:'']),
    html:`<section class="slide hero-slide active"><div class="hero-copy"><div class="eyebrow">${esc(b.tv_intro_kicker||'KARACHUONYO CONSTITUENCY IMPACT')}</div><h1>${esc(b.tv_intro_headline||'Visible projects. Clear public record.')}</h1><p>${esc(trim(b.tv_intro_subheadline||'A live view of projects, locations, photos, videos and documented impact across Karachuonyo.',180))}</p><div class="hero-line"><span>PROJECTS</span><span>WARDS</span><span>IMPACT</span><span>EVIDENCE</span></div></div><div class="mp-card">${portrait}<div class="mp-info"><small>${esc((b.leader_title||'MEMBER OF PARLIAMENT').toUpperCase())}</small><b>${esc(b.leader||'Hon. Andrew Adipo Okuome')}</b><span>${esc(jurisdiction)}</span></div></div></section>`
  }];

  (data.projects||[]).forEach(p=>{
    (p.media||[]).filter(m=>m.type==='video'&&m.url).forEach(m=>slides.push(videoSlide(p,m,b)));
    (p.media||[]).filter(m=>m.type==='image'&&m.url).forEach(m=>slides.push(imageSlide(p,m,b)));
    const title=bi(p.short_title,p.short_title_local,'h2',96),summary=bi(p.summary,p.summary_local,'p',142);
    slides.push({
      duration:9000,ticker:projectTicker(p,b),
      html:`<section class="slide record-slide"><div class="record-layout"><div><div class="eyebrow">${esc(p.sector)} · ${esc(wardLabel(p))}</div>${title}${summary}<div class="route-chip">📍 ${esc(trim(locationLabel(p),130))}</div>${b.tv_show_website?`<br><a class="open-record" href="${esc(p.url+localModeQuery())}">FULL PROJECT RECORD →</a>`:''}</div><div class="record-facts"><div class="record-fact"><span>WARD</span><b>${esc(wardLabel(p))}</b></div><div class="record-fact"><span>INTERVENTION</span><b>${esc(trim(pick(p.intervention,p.intervention_local)||p.sector,78))}</b></div><div class="record-fact"><span>RECORD ID</span><b>${esc(p.id)}</b></div></div></div></section>`
    });
    if(p.impacts?.length){
      const cards=p.impacts.slice(0,3).map((x,n)=>{const local=x.local||'',content=lang()==='bilingual'&&local?`<span>${esc(trim(x.en,92))}</span><small>${esc(trim(local,92))}</small>`:`<span>${esc(trim(pick(x.en,local),92))}</span>`;return `<div class="metric"><strong>0${n+1}</strong>${content}</div>`}).join('');
      slides.push({duration:9000,ticker:projectTicker(p,b,'Project impact and results'),html:`<section class="slide impact-slide"><div class="eyebrow">PROJECT IMPACT · ${esc(wardLabel(p))}</div><h2>What is changing on the ground.</h2><div class="metrics">${cards}</div></section>`});
    }
  });

  slides.push(constituencyPulseSlide(data,b));
  slides.push({duration:9000,ticker:joinTicker(['Projects','Exact locations','Photos','Videos','Evidence',domain?`Explore the full record: ${domain}`:'']),html:`<section class="slide closing-slide"><div class="eyebrow">PUBLIC IMPACT RECORD</div><h2>See the project.<br>Explore the evidence.</h2><p>Projects · exact locations · photos · videos · maps · supporting documents</p>${b.tv_show_qr||b.tv_show_website?`<div class="closing-domain">${b.tv_show_qr?`<img src="/qr/" alt="QR">`:''}${b.tv_show_website?`<div><small>SCAN OR VISIT</small><b>${esc(domain)}</b></div>`:''}</div>`:''}<div class="disclaimer">PUBLIC PROJECT INFORMATION DISPLAYED FROM THE ADIPO DELIVERS IMPACT PLATFORM.</div></section>`});

  stage.innerHTML=slides.map((s,idx)=>`<div class="slide-wrap" data-index="${idx}">${s.html}</div>`).join('');
  nodes=[...stage.querySelectorAll('.slide')];
  i=0;activate(0);
}

function updateTicker(index){
  const ticker=document.getElementById('tickerText');
  if(!ticker)return;
  ticker.textContent=slides[index]?.ticker||dataCache?.brand?.tv_ticker_text||'';
  ticker.style.animation='none';
  void ticker.offsetWidth;
  const length=ticker.textContent.length;
  const seconds=Math.max(24,Math.min(58,Math.round(length/5.2)));
  ticker.style.animation=`ticker ${seconds}s linear infinite`;
}

function activate(index){
  if(!nodes.length)return;
  nodes.forEach((n,idx)=>{
    const active=idx===index;n.classList.toggle('active',active);
    const vid=n.querySelector('video');if(vid){if(active){vid.currentTime=0;vid.play().catch(()=>{})}else{vid.pause()}}
  });
  updateTicker(index);
  const slideNo=document.getElementById('slideNo');if(slideNo)slideNo.textContent=`${index+1} / ${nodes.length}`;
  const bar=document.getElementById('progressBar');if(bar){bar.style.transition='none';bar.style.width='0%';requestAnimationFrame(()=>requestAnimationFrame(()=>{bar.style.transition=`width ${slides[index].duration}ms linear`;bar.style.width='100%'}));}
  clearTimeout(timer);timer=setTimeout(()=>{i=(i+1)%nodes.length;activate(i)},slides[index].duration);
}

fetch(window.TV_PLAYLIST_URL).then(r=>r.json()).then(build).catch(e=>{stage.innerHTML='<div class="loading">Unable to load the TV playlist.</div>';console.error(e)});
document.addEventListener('keydown',e=>{if(!nodes.length)return;if(e.key==='ArrowRight'){i=(i+1)%nodes.length;activate(i)}if(e.key==='ArrowLeft'){i=(i-1+nodes.length)%nodes.length;activate(i)}if(e.key.toLowerCase()==='f'){document.documentElement.requestFullscreen?.()}});
