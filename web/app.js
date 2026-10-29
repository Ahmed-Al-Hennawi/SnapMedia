(function(){
  'use strict';
  const $ = id => document.getElementById(id);
  const body=document.body;
  const urlInput=$('video-url');
  const form=$('download-form');
  const result=$('result-section');
  const progress=$('progress-dialog');
  const status=$('form-status');
  const toastEl=$('toast');
  let platform='tiktok';
  let metadata=null;
  let busy=false;
  let inputRevision=0;
  let toastTimer;

  function t(key){return window.snapT(key);}
  function toast(msg){clearTimeout(toastTimer);toastEl.textContent=msg;toastEl.classList.add('show');toastTimer=setTimeout(()=>toastEl.classList.remove('show'),3200);}
  function showError(msg){status.textContent=msg;status.hidden=false;}
  function clearError(){status.hidden=true;status.textContent='';}
  function setPlatform(next){
    if(!['tiktok','youtube','instagram','facebook'].includes(next)) return;
    platform=next;
    body.dataset.platform=next;
    const colours={tiktok:'#0b0c12',instagram:'#faf8fc',youtube:'#f9fafc',facebook:'#f7f9ff'};
    $('theme-color').content=colours[next];
    document.querySelectorAll('[data-platform-option]').forEach(btn=>{
      const active=btn.dataset.platformOption===next;
      btn.classList.toggle('active',active);
      btn.setAttribute('aria-selected',String(active));
    });
    updatePlaceholder();
    if(metadata && metadata.platform!==next){metadata=null;result.hidden=true;}
  }
  function detectPlatform(raw){
    try{
      const parsed=new URL(raw.trim());
      if(parsed.protocol!=='https:') return null;
      const host=parsed.hostname.toLowerCase().replace(/\.$/,'');
      const matches=(value)=> host===value||host.endsWith('.'+value);
      if(matches('tiktok.com')||matches('tiktokv.com')) return 'tiktok';
      if(matches('youtube.com')||matches('youtu.be')) return 'youtube';
      if(matches('instagram.com')||matches('instagr.am')) return 'instagram';
      if(matches('facebook.com')||matches('fb.watch')||matches('fb.com')||matches('facebook.watch')) return 'facebook';
    }catch(_){/* not a URL yet */}
    return null;
  }
  function updatePlaceholder(){
    const example={tiktok:'https://www.tiktok.com/@creator/video/...',instagram:'https://www.instagram.com/reel/...',youtube:'https://www.youtube.com/shorts/...',facebook:'https://www.facebook.com/reel/...'};
    urlInput.placeholder=example[platform];
  }
  function setFormat(){
    document.querySelectorAll('.format-card').forEach(label=>label.classList.toggle('selected',label.querySelector('input').checked));
    const mp3=document.querySelector('input[name="media-format"]:checked').value==='mp3';
    $('standard-desc').textContent=mp3?'MP3 · 128 kbps':'MP4 · Up to 720p';
    $('hd-desc').textContent=mp3?'MP3 · 192 kbps':'MP4 · Up to 1080p';
  }
  async function api(path,method='GET',payload){
    const options={method,headers:{'Accept':'application/json'}};
    if(payload!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(payload);}
    const response=await fetch((window.SNAP_CONFIG?.apiBase||'')+path,options);
    let data;
    try{data=await response.json();}catch(_){throw new Error('The server is not responding. Start the Python backend first.');}
    if(!response.ok)throw new Error(data.error||t('error'));
    return data;
  }
  function formatDuration(seconds){
    if(!Number.isFinite(seconds))return '';
    const min=Math.floor(seconds/60),sec=seconds%60;
    return `${min}:${String(sec).padStart(2,'0')}`;
  }
  function showResult(info){
    metadata=info;
    clearError();
    const thumb=$('media-thumbnail');
    thumb.hidden=!info.thumbnail;
    $('preview-fallback').hidden=!!info.thumbnail;
    if(info.thumbnail){thumb.referrerPolicy='no-referrer';thumb.src=info.thumbnail;thumb.onerror=()=>{thumb.hidden=true;$('preview-fallback').hidden=false;};}
    $('media-title').textContent=info.title;
    $('media-creator').textContent=info.uploader||info.platform;
    $('media-duration').textContent=info.duration?formatDuration(info.duration):'';
    result.hidden=false;
    setFormat();
    result.scrollIntoView({behavior:'smooth',block:'center'});
  }
  async function analyze(event){
    event.preventDefault();
    if(busy)return;
    const url=urlInput.value.trim();
    const found=detectPlatform(url);
    if(!found){showError(t('invalid'));urlInput.focus();return;}
    setPlatform(found);
    result.hidden=true;metadata=null;
    clearError();busy=true;
    $('analyze-button').disabled=true;
    const label=$('analyze-button').querySelector('span');
    label.textContent=t('loading');
    const revision=inputRevision;
    try{
      const info=await api('/api/info','POST',{url});
      if(revision===inputRevision) showResult(info);
    }
    catch(err){if(revision===inputRevision) showError(err.message||t('error'));}
    finally{busy=false;$('analyze-button').disabled=false;label.textContent=t('getOptions');}
  }
  function progressUpdate(percent){
    const amount=Math.max(1,Math.min(100,Number(percent)||1));
    $('progress-bar').style.width=amount+'%';
    $('progress-percent').textContent=amount+'%';
  }
  function triggerFileDownload(url,name){
    const anchor=document.createElement('a');
    anchor.href=url;anchor.download=name||'SnapMedia';
    document.body.append(anchor);anchor.click();anchor.remove();
  }
  function setupCoffeeWidget(){
    const toggle=$('coffee-toggle'),panel=$('coffee-panel'),close=$('coffee-close');
    let supportUrl='';
    try{
      const parsed=new URL(window.SNAP_CONFIG?.buyMeACoffeeUrl||'');
      if(parsed.protocol==='https:' && ['buymeacoffee.com','www.buymeacoffee.com'].includes(parsed.hostname) && parsed.pathname!=='/') supportUrl=parsed.href;
    }catch(_){/* Link will be added after the support account is shared. */}
    if(supportUrl){
      for(const id of ['coffee-section-link','coffee-widget-link']){$(id).href=supportUrl;$(id).hidden=false;}
      $('coffee-section-pending').hidden=true;
      $('coffee-widget-pending').hidden=true;
    }
    const setOpen=open=>{panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open));};
    if('IntersectionObserver' in window){
      const widget=document.querySelector('.coffee-widget');
      const smallScreen=window.matchMedia('(max-width:680px)');
      let formVisible=false;
      const updateVisibility=()=>{
        const shelved=smallScreen.matches && formVisible;
        widget.classList.toggle('coffee-widget-shelved',shelved);
        if(shelved)setOpen(false);
      };
      new IntersectionObserver(([entry])=>{formVisible=entry.isIntersecting;updateVisibility();}).observe(form);
      smallScreen.addEventListener('change',updateVisibility);
    }
    toggle.addEventListener('click',()=>setOpen(panel.hidden));
    close.addEventListener('click',()=>{setOpen(false);toggle.focus();});
    document.addEventListener('click',event=>{if(!event.target.closest('.coffee-widget'))setOpen(false);});
    document.addEventListener('keydown',event=>{if(event.key==='Escape' && !panel.hidden){setOpen(false);toggle.focus();}});
  }
  async function beginDownload(quality){
    if(!metadata||busy)return;
    busy=true;
    const buttons=document.querySelectorAll('[data-quality]');
    buttons.forEach(button=>button.disabled=true);
    try {
      const format=document.querySelector('input[name="media-format"]:checked').value;
      if(format==='mp4'){
        const health=await api('/api/health');
        if(health.media_pipeline!=='h264-aac-verified'){
          throw new Error('The download server needs a restart to provide playable MP4 videos.');
        }
        if(!health.h264_encoder){
          throw new Error('The server needs FFmpeg with libx264 to prepare playable MP4 videos.');
        }
      }
      progress.showModal();progressUpdate(3);
      $('progress-detail').textContent=t('progressText');
      const job=await api('/api/download','POST',{url:metadata.url,format,quality});
      await trackJob(job.id);
    }catch(err){
      if(progress.open) progress.close();
      showError(err.message||t('error'));toast(err.message||t('error'));
    }finally{busy=false;buttons.forEach(button=>button.disabled=false);}
  }
  async function trackJob(id){
    const began=Date.now();
    while(Date.now()-began<30*60*1000){
      const state=await api('/api/jobs/'+encodeURIComponent(id));
      progressUpdate(state.progress||3);
      if(state.status==='ready'){
        progressUpdate(100);
        if(progress.open)progress.close();
        triggerFileDownload(state.download_url,state.filename);
        toast(t('ready'));
        return;
      }
      if(state.status==='error')throw new Error(state.error||t('error'));
      await new Promise(resolve=>setTimeout(resolve,1150));
    }
    throw new Error('This download timed out. Try a shorter video.');
  }
  function wire(){
    window.snapInitializeLanguages();
    const syncClearButton=()=>$('url-field').classList.toggle('has-value',Boolean(urlInput.value));
    syncClearButton();
    setPlatform(platform);
    setFormat();
    $('year').textContent=new Date().getFullYear();
    document.querySelectorAll('[data-platform-option]').forEach(btn=>btn.addEventListener('click',()=>setPlatform(btn.dataset.platformOption)));
    document.querySelectorAll('input[name="media-format"]').forEach(input=>input.addEventListener('change',setFormat));
    urlInput.addEventListener('input',()=>{
      inputRevision++;
      syncClearButton();
      const found=detectPlatform(urlInput.value);if(found)setPlatform(found);
      clearError();if(metadata){metadata=null;result.hidden=true;}
    });
    window.addEventListener('pageshow',syncClearButton);
    $('clear-button').addEventListener('click',()=>{
      urlInput.value='';
      urlInput.dispatchEvent(new Event('input',{bubbles:true}));
      urlInput.focus();
    });
    $('paste-button').addEventListener('click',async()=>{
      try{
        const pasted=await navigator.clipboard.readText();
        if(!pasted)throw Error();
        urlInput.value=pasted;
        urlInput.dispatchEvent(new Event('input'));
        toast(t('copied'));
      }catch(_){toast(t('pasteDenied'));urlInput.focus();}
    });
    form.addEventListener('submit',analyze);
    document.querySelectorAll('[data-quality]').forEach(btn=>btn.addEventListener('click',()=>beginDownload(btn.dataset.quality)));
    $('progress-close').addEventListener('click',()=>progress.close());
    const menu=$('mobile-nav'),toggle=$('menu-toggle');
    toggle.addEventListener('click',()=>{menu.hidden=!menu.hidden;toggle.setAttribute('aria-expanded',String(!menu.hidden));});
    menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false');}));
    document.addEventListener('snap:language',()=>{setFormat();updatePlaceholder();});
    setupCoffeeWidget();
  }
  wire();
})();
