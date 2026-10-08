const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stage=document.getElementById('stage');
let slides=[],nodes=[],i=0,timer=null,dataCache=null;
let soundEnabled=false;

const trim=(s,n=160)=>{s=String(s||'').replace(/\s+/g,' ').trim();return s.length>n?s.slice(0,n-1).trim()+'…':s};
const clean=s=>String(s||'').replace(/\s+/g,' ').trim();
function lang(){return dataCache?.language?.mode||window.TV_LANGUAGE_MODE||'en'}
function pick(en,local){return lang()==='local'?(local||en||''):(en||local||'')}
function bi(en,local,tag='div',max=170){
  en=trim(en,max);local=trim(local,max);
  if(lang()==='bilingual'&&local&&local!==en){
    return `<${tag}><span>${esc(en)}</span><small>${esc(local)}</small></${tag}>`;
  }
  return `<${tag}>${esc(trim(pick(en,local),max))}</${tag}>`;
}
function wardLabel(p){return pick(p.ward,p.ward_local)}
function locationLabel(p){return pick(p.location,p.location_local)}
function money(v){const n=Number(v);return Number.isFinite(n)&&n>0?`KES ${new Intl.NumberFormat('en-KE',{maximumFractionDigits:0}).format(n)}`:''}
function ticker(parts){return parts.map(clean).filter(Boolean).join('   •   ')}

function updateClock(){
  const d=new Date();
  const c=document.getElementById('clock');
  const dl=document.getElementById('dateLabel');
  if(c)c.textContent=d.toLocaleTimeString('en-KE',{hour:'2-digit',minute:'2-digit'});
  if(dl)dl.textContent=d.toLocaleDateString('en-KE',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase();
}
updateClock();setInterval(updateClock,1000);

function updateSoundStatus(){
  const box=document.getElementById('soundStatus');
  const icon=document.getElementById('soundStatusIcon');
  const text=document.getElementById('soundStatusText');
  if(!box||!icon||!text)return;
  box.classList.toggle('enabled',soundEnabled);
  icon.textContent=soundEnabled?'🔊':'🔇';
  text.textContent=soundEnabled?'Sound enabled':'Sound waiting';
}
function unlockSound(){
  soundEnabled=true;
  document.getElementById('soundGate')?.classList.add('hidden');
  document.querySelectorAll('video').forEach(v=>{v.muted=false;v.volume=1.0;});
  updateSoundStatus();
  const video=nodes[i]?.querySelector('video');
  if(video){video.muted=false;video.volume=1.0;video.play().catch(()=>{});}
}
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('enableSoundBtn')?.addEventListener('click',unlockSound);
  updateSoundStatus();
});

function projectTicker(p,b,extra=''){
  const impacts=(p.impacts||[]).slice(0,2).map(x=>pick(x.en,x.local)).filter(Boolean);
  return ticker([
    p.short_title||p.title,
    `${p.sector||'Project'} — ${wardLabel(p)}`,
    locationLabel(p),
    p.intervention,
    p.budget?`Investment: ${money(p.budget)}`:'',
    p.funding_source?`Funding: ${p.funding_source}`:'',
    p.implementing_agency?`Implementing agency: ${p.implementing_agency}`:'',
    p.beneficiaries?`Beneficiaries: ${Number(p.beneficiaries).toLocaleString('en-KE')}`:'',
    impacts.length?`Impact: ${impacts.join(' / ')}`:'',
    extra,
    b.tv_show_website&&b.domain?`More: ${b.domain}`:''
  ]);
}

function fitProjectPhoto(img){
  if(!img||!img.naturalWidth||!img.naturalHeight)return;
  const ratio=img.naturalWidth/img.naturalHeight;
  img.dataset.fit=(ratio>=1.42)?'cover':'contain';
}
window.fitProjectPhoto=fitProjectPhoto;

function statusLabel(p){
  if(p.verification==='verified')return 'VERIFIED';
  if(p.completion_date)return 'COMPLETED';
  return 'IN PROGRESS';
}
function sectorIcon(sector){
  const s=String(sector||'').toLowerCase();
  if(s.includes('education'))return '📘';
  if(s.includes('road')||s.includes('transport'))return '🛣️';
  if(s.includes('water'))return '💧';
  if(s.includes('health'))return '✚';
  if(s.includes('agric'))return '🌱';
  return '◆';
}
function projectDetails(p){
  const rows=[];
  rows.push(['●','Ward',wardLabel(p)]);
  rows.push(['●','Location',locationLabel(p)]);
  if(p.budget) rows.push(['●','Investment',money(p.budget)]);
  if(p.funding_source) rows.push(['●','Funding',p.funding_source]);
  if(p.implementing_agency) rows.push(['●','Implementing',p.implementing_agency]);
  if(p.beneficiaries) rows.push(['●','Beneficiaries',Number(p.beneficiaries).toLocaleString('en-KE')]);
  rows.push(['●','Status',statusLabel(p)]);
  const impact=(p.impacts||[])[0];
  if(impact) rows.push(['●','Impact',pick(impact.en,impact.local)]);
  return rows.slice(0,4);
}

function splitProjectSlide(p,m,b){
  const details=projectDetails(p);
  return {
    duration:Math.max(10000,(m?.duration||12)*1000),
    ticker:projectTicker(p,b,m?.caption||''),
    html:`<section class="slide project-split" style="--photo:url('${esc(m.url)}')">
      <div class="project-photo-panel">
        <div class="project-photo-bg"></div>
        <div class="project-photo-main">
          <img src="${esc(m.url)}" alt="${esc(m.title||p.short_title)}" onload="fitProjectPhoto(this)" data-fit="cover">
        </div>
        <div class="project-photo-shade"></div>
        <div class="photo-label">${esc(wardLabel(p))}</div>
      </div>

      <div class="project-info-panel">
        <div class="info-top">
          <div class="sector-line">
            <div class="sector-icon">${sectorIcon(p.sector)}</div>
            <div class="sector-name">${esc(p.sector||'PROJECT')}</div>
          </div>
          <div class="status-pill">${esc(statusLabel(p))}</div>
        </div>
        <h2>${esc(trim(p.short_title||p.title,92))}</h2>
        <div class="project-summary">${esc(trim(m.caption||p.summary,220))}</div>
        <div class="details-block">
          <div class="details-title">PROJECT DETAILS</div>
          <div class="details-card">
            ${details.map(([ic,l,v])=>`
              <div class="detail-row">
                <div class="detail-icon">${ic}</div>
                <div class="detail-label">${esc(l)}:</div>
                <div class="detail-value">${esc(trim(v,110))}</div>
              </div>`).join('')}
          </div>
        </div>
      </div>
    </section>`
  };
}

function sloganTransition(b,jurisdiction){
  const slogan=clean(b.tagline);
  const leader=clean(b.leader)||'Hon. Andrew Adipo Okuome';
  return {
    duration:4000,
    ticker:ticker([slogan,jurisdiction]),
    html:`<section class="slide slogan-transition">
      <div class="slogan-glow slogan-glow-one"></div>
      <div class="slogan-glow slogan-glow-two"></div>
      <div class="slogan-transition-inner">
        ${b.logo?`<div class="transition-logo-wrap"><img class="transition-logo" src="${esc(b.logo)}" alt="${esc(leader)}"></div>`:''}
        <div class="transition-name">${esc(leader.toUpperCase())}</div>
        <div class="transition-rule"></div>
        <div class="transition-slogan">${esc(slogan)}</div>
        <div class="transition-jurisdiction">${esc(jurisdiction)}</div>
      </div>
    </section>`
  };
}

function bursaryMoney(v){
  const n=Number(v||0);
  if(!Number.isFinite(n)||n<=0)return '—';
  if(n>=1000000)return `KES ${(n/1000000).toFixed(n>=10000000?1:2).replace(/\.0+$/,'')}M`;
  if(n>=1000)return `KES ${(n/1000).toFixed(0)}K`;
  return `KES ${n.toLocaleString('en-KE')}`;
}

function bursaryOverviewSlide(data,b){
  const x=data.bursary||{};
  const periods=(x.periods||[]).join(' · ');
  return {
    duration:11000,
    ticker:ticker([
      `${Number(x.students||0).toLocaleString('en-KE')} students supported`,
      `${x.wards_reached||0} wards`,
      Number(x.amount||0)>0?`${bursaryMoney(x.amount)} verified bursary allocation`:'',
      periods?`Reporting period: ${periods}`:'',
      b.domain?`Explore: ${b.domain}`:''
    ]),
    html:`<section class="slide bursary-overview">
      <div class="bursary-overview-copy">
        <div class="bursary-kicker">EDUCATION SUPPORT · BURSARY IMPACT</div>
        <h2>Investing in<br><span>Karachuonyo's future.</span></h2>
        <p>Verified ward-level education support shown as aggregate public-impact figures.</p>
        <div class="bursary-period">${esc(periods||'Current verified reporting period')}</div>
      </div>
      <div class="bursary-hero-metrics">
        <div class="bursary-big-card primary"><small>STUDENTS SUPPORTED</small><strong>${Number(x.students||0).toLocaleString('en-KE')}</strong><span>Across verified ward records</span></div>
        <div class="bursary-big-card"><small>VERIFIED ALLOCATION</small><strong>${esc(bursaryMoney(x.amount))}</strong><span>Education bursary support</span></div>
        <div class="bursary-mini-grid">
          <div><strong>${x.wards_reached||0}</strong><span>Wards reached</span></div>
          <div><strong>${Number(x.secondary||0).toLocaleString('en-KE')}</strong><span>Secondary</span></div>
          <div><strong>${Number(x.college_tvet||0).toLocaleString('en-KE')}</strong><span>College / TVET</span></div>
          <div><strong>${Number(x.university||0).toLocaleString('en-KE')}</strong><span>University</span></div>
        </div>
      </div>
    </section>`
  };
}

function bursaryWardSlide(data,b){
  const x=data.bursary||{}, rows=x.wards||[];
  const max=Math.max(1,...rows.map(r=>Number(r.students||0)));
  const bars=rows.map((r,idx)=>{
    const width=Math.max(3,Math.round((Number(r.students||0)/max)*100));
    return `<div class="ward-bursary-row">
      <div class="ward-bursary-rank">${String(idx+1).padStart(2,'0')}</div>
      <div class="ward-bursary-name"><b>${esc(r.ward)}</b><span>${esc(r.period||'')}</span></div>
      <div class="ward-bursary-bar"><i style="width:${width}%"></i></div>
      <div class="ward-bursary-count"><strong>${Number(r.students||0).toLocaleString('en-KE')}</strong><span>students</span></div>
      <div class="ward-bursary-money">${Number(r.amount||0)>0?esc(bursaryMoney(r.amount)):'—'}</div>
    </div>`;
  }).join('');
  return {
    duration:12000,
    ticker:ticker(rows.map(r=>`${r.ward}: ${Number(r.students||0).toLocaleString('en-KE')} students`).concat([b.domain?`More: ${b.domain}`:''])),
    html:`<section class="slide bursary-wards">
      <div class="bursary-ward-head">
        <div><div class="bursary-kicker">WARD-BY-WARD BURSARY REACH</div><h2>Education support across the constituency.</h2></div>
        <div class="bursary-total-chip"><strong>${Number(x.students||0).toLocaleString('en-KE')}</strong><span>Total students</span></div>
      </div>
      <div class="ward-bursary-list">${bars}</div>
      <div class="bursary-footnote">Verified aggregate figures only · No individual student records displayed</div>
    </section>`
  };
}

function build(data){
  dataCache=data;
  const b=data.brand||{};
  const projects=data.projects||[];
  const domain=b.domain||location.host;
  const jurisdiction=b.jurisdiction||'Karachuonyo Constituency';

  let portrait='';
  if(b.tv_show_leader_photo&&b.leader_photo){
    portrait=`<div class="leader-photo"><img src="${esc(b.leader_photo)}" alt="${esc(b.leader||'Member of Parliament')}"></div>`;
  }else{
    portrait=`<div class="leader-photo"></div>`;
  }

  slides=[{
    duration:Math.max(7000,(b.tv_intro_duration_seconds||9)*1000),
    ticker:ticker([b.tv_ticker_text||'Karachuonyo development impact',`${projects.length} project records`,jurisdiction]),
    html:`<section class="slide hero-slide active">
      <div>
        <div class="eyebrow">${esc(b.tv_intro_kicker||'KARACHUONYO CONSTITUENCY IMPACT')}</div>
        <h1>${esc(b.tv_intro_headline||'Visible projects. Clear public record.')}</h1>
        <p>${esc(trim(b.tv_intro_subheadline||'Projects, places, progress and evidence from across the constituency.',180))}</p>
        ${b.tagline?`<div class="hero-slogan">${esc(b.tagline)}</div>`:''}
      </div>
      <div class="leader-card">
        ${portrait}
        <div class="leader-meta">
          <small>${esc((b.leader_title||'MEMBER OF PARLIAMENT').toUpperCase())}</small>
          <b>${esc(b.leader||'Hon. Andrew Adipo Okuome')}</b>
          <span>${esc(jurisdiction)}</span>
        </div>
      </div>
    </section>`
  }];

  if(data.bursary?.wards?.length){
    slides.push(bursaryOverviewSlide(data,b));
    slides.push(bursaryWardSlide(data,b));
  }

  projects.forEach((p,projectIndex)=>{
    const images=(p.media||[]).filter(m=>m.type==='image'&&m.url);
    const videos=(p.media||[]).filter(m=>m.type==='video'&&m.url);

    images.forEach(m=>slides.push(splitProjectSlide(p,m,b)));

    videos.forEach(m=>{
      const poster=m.poster||'';
      slides.push({
        duration:Math.max(10000,(m.end||m.duration||15)*1000),
        ticker:projectTicker(p,b,m.caption||''),
        html:`<section class="slide project-split">
          <div class="project-photo-panel">
            <video class="project-video" playsinline preload="auto" ${poster?`poster="${esc(poster)}"`:''}>
              <source src="${esc(m.url)}" type="video/mp4">
            </video>
            <div class="video-audio-badge">FULL AUDIO</div>
          </div>
          <div class="project-info-panel">
            <div class="info-top">
              <div class="sector-line"><div class="sector-icon">${sectorIcon(p.sector)}</div><div class="sector-name">${esc(p.sector||'PROJECT')}</div></div>
              <div class="status-pill">${esc(statusLabel(p))}</div>
            </div>
            <h2>${esc(trim(p.short_title||p.title,92))}</h2>
            <div class="project-summary">${esc(trim(m.caption||p.summary,220))}</div>
            <div class="details-block">
              <div class="details-title">PROJECT DETAILS</div>
              <div class="details-card">
                ${projectDetails(p).map(([ic,l,v])=>`<div class="detail-row"><div class="detail-icon">${ic}</div><div class="detail-label">${esc(l)}:</div><div class="detail-value">${esc(trim(v,110))}</div></div>`).join('')}
              </div>
            </div>
          </div>
        </section>`
      });
    });

    if(b.tagline&&(projectIndex+1)%3===0&&projectIndex<projects.length-1){
      slides.push(sloganTransition(b,jurisdiction));
    }
  });

  slides.push({
    duration:9000,
    ticker:ticker(['Projects','Locations','Photos','Videos','Progress','Evidence',domain?`Explore: ${domain}`:'']),
    html:`<section class="slide closing-slide">
      <div>
        <div class="eyebrow">PUBLIC IMPACT RECORD</div>
        <h2>See the project.<br>Explore the evidence.</h2>
        <p>Projects · locations · progress · photos · videos · supporting evidence</p>
        ${b.tagline?`<div class="closing-slogan">${esc(b.tagline)}</div>`:''}
        ${b.tv_show_qr||b.tv_show_website?`<div class="closing-cta">
          ${b.tv_show_qr?`<img src="/qr/" alt="QR code">`:''}
          ${b.tv_show_website?`<div><small>SCAN OR VISIT</small><b>${esc(domain)}</b></div>`:''}
        </div>`:''}
      </div>
    </section>`
  });

  stage.innerHTML=slides.map((s,idx)=>`<div class="slide-wrap" data-index="${idx}">${s.html}</div>`).join('');
  nodes=[...stage.querySelectorAll('.slide')];
  document.querySelectorAll('video').forEach(v=>{v.muted=!soundEnabled;v.volume=soundEnabled?1.0:0.0;});
  i=0;activate(0);
}

function updateTicker(idx){
  const el=document.getElementById('tickerText');
  if(!el)return;
  el.textContent=slides[idx]?.ticker||dataCache?.brand?.tv_ticker_text||'';
  el.style.animation='none';void el.offsetWidth;
  const secs=Math.max(24,Math.min(62,Math.round(el.textContent.length/5)));
  el.style.animation=`ticker ${secs}s linear infinite`;
}

function activate(idx){
  if(!nodes.length)return;
  nodes.forEach((n,j)=>{
    const active=j===idx;
    n.classList.toggle('active',active);
    const v=n.querySelector('video');
    if(v){if(active){v.currentTime=0;v.muted=!soundEnabled;v.volume=soundEnabled?1.0:0.0;v.play().catch(()=>{})}else{v.pause();v.currentTime=0}}
  });
  updateTicker(idx);
  clearTimeout(timer);
  timer=setTimeout(()=>{i=(idx+1)%nodes.length;activate(i)},slides[idx].duration);
}

fetch(window.TV_PLAYLIST_URL)
  .then(r=>{if(!r.ok)throw new Error(`Playlist ${r.status}`);return r.json()})
  .then(build)
  .catch(err=>{
    console.error(err);
    stage.innerHTML='<div class="loading">Unable to load the TV playlist.</div>';
  });

document.addEventListener('keydown',e=>{
  if(!nodes.length)return;
  if(e.key==='ArrowRight'){i=(i+1)%nodes.length;activate(i)}
  if(e.key==='ArrowLeft'){i=(i-1+nodes.length)%nodes.length;activate(i)}
  if(e.key.toLowerCase()==='f'){document.documentElement.requestFullscreen?.()}
  if(e.key.toLowerCase()==='m'){soundEnabled=!soundEnabled;document.querySelectorAll('video').forEach(v=>{v.muted=!soundEnabled;v.volume=soundEnabled?1.0:0.0;});updateSoundStatus();}
});
