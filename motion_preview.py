"""Local motion sampling. Standard library only; FFmpeg does video decoding."""
import json
import math
import subprocess
import tempfile
from pathlib import Path


def intervals_from_scores(scores, start, end, sensitivity):
    threshold = {'low': .06, 'medium': .025, 'high': .008}.get(sensitivity, .025)
    active = [t for t, score in scores if score >= threshold]
    events = []
    for t in active:
        left, right = max(start, t - .75), min(end, t + .75)
        if events and left <= events[-1][1] + .5:
            events[-1][1] = max(events[-1][1], right)
        else:
            events.append([left, right])
    return events


def choose_times(events, count):
    """Distribute budget across separate events, not just highest single peak."""
    if not events or count < 1:
        return []
    if len(events) > count:
        events = [events[min(len(events)-1, int((i+.5)*len(events)/count))] for i in range(count)]
    quotas = [count // len(events) + (i < count % len(events)) for i in range(len(events))]
    return sorted(a + (b-a)*(j+.5)/q for (a,b),q in zip(events,quotas) for j in range(q))


def analyze(video, start, end, sensitivity, ffmpeg):
    # Bound scan work to 10 minutes per request. Caller controls interval.
    if end-start > 600:
        raise ValueError('Intervallo analisi movimento massimo: 600 secondi')
    cmd = [ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-ss', str(start),
           '-i', str(video), '-t', str(end-start), '-an', '-vf',
           'fps=2,scale=160:90:flags=area,format=gray', '-threads', '1',
           '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1']
    result = subprocess.run(cmd, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-1000:])
    size=160*90
    if len(result.stdout) < size*2:
        return [], []
    previous=result.stdout[:size];scores=[]
    for i in range(1,len(result.stdout)//size):
        frame=result.stdout[i*size:(i+1)*size]
        # Remove uniform brightness drift; suppress small per-pixel noise.
        delta=[a-b for a,b in zip(frame,previous)]
        drift=sum(delta)/size
        score=sum(abs(d-drift)>14 for d in delta)/size
        scores.append((min(end,start+i/2),score));previous=frame
    return intervals_from_scores(scores,start,end,sensitivity),scores


def generate(video, target, duration, config, ffmpeg, uniform, logger):
    target=Path(target)
    wanted=max(3,min(60,int(config.get('motion_frames',30))))
    total=max(1.,min(60.,float(config.get('motion_seconds',7))))
    end=max(.001,float(duration))
    start=min(1.,max(0.,end-.001))
    effective=dict(config,preview_start=start,preview_end=end,preview_frames=wanted,preview_seconds=total)
    events=[];scores=[];fallback=None
    try:
        events,scores=analyze(video,start,end,config.get('motion_sensitivity','medium'),ffmpeg)
    except Exception as exc:
        fallback='analysis_error: '+str(exc)
    times=choose_times(events,wanted)
    report={'mode':'motion','sensitivity':config.get('motion_sensitivity','medium'),
            'interval':[start,end],'events':events,'selected_seconds':times,
            'fallback':fallback,'person_detection':False}
    target.parent.mkdir(parents=True,exist_ok=True)
    if not times:
        report['fallback']=fallback or 'no_significant_motion'
        uniform(video,target,duration,effective)
    else:
        # Separate temp directory, publish only after successful encode.
        try:
            with tempfile.TemporaryDirectory(prefix='v380_motion_') as td:
                td=Path(td)
                for i,t in enumerate(times):
                    out=td/('frame_%03d.png'%i)
                    r=subprocess.run([ffmpeg,'-nostdin','-y','-hide_banner','-loglevel','error',
                        '-ss',str(t),'-i',str(video),'-frames:v','1','-vf','scale=480:-2',
                        '-threads','1',str(out)],capture_output=True,timeout=40)
                    if r.returncode or not out.exists():
                        raise RuntimeError('Estrazione fotogramma movimento fallita')
                delay=max(2,round(total*100/len(times)))
                rate=100/delay
                temp=td/'preview.gif'
                r=subprocess.run([ffmpeg,'-nostdin','-y','-hide_banner','-loglevel','error',
                    '-framerate',str(rate),'-i',str(td/'frame_%03d.png'),'-filter_complex_threads','1',
                    '-vf','split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer',
                    '-loop','0','-final_delay',str(delay),str(temp)],capture_output=True,timeout=120)
                if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1000:])
                # copy then replace in target directory (temp dir may be on another filesystem)
                import shutil
                pending=target.with_suffix('.pending.gif')
                shutil.copyfile(temp,pending);pending.replace(target)
                report['gif_duration_approx']=len(times)*delay/100
        except Exception as exc:
            report['fallback']='render_error: '+str(exc)
            uniform(video,target,duration,effective)
    target.with_suffix('.motion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    logger('MOTION PREVIEW events=%d frames=%d fallback=%s'%(len(events),len(times),report['fallback']))
    return report
