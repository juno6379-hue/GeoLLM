"""Scientific pilot figures; no zero-filled placeholders."""
from .build_tables import write_table
from ..evaluation.metrics import distribution
from collections import Counter


def build_operational_figure(root, rows):
    """Measured diagnostics only: incomparable component cohorts, no speed ranking."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    records=[]
    for method in sorted({r.get('method','UNSPECIFIED') for r in rows}):
        group=[r for r in rows if r.get('method','UNSPECIFIED')==method]
        statuses=Counter(str(r.get('status','UNKNOWN')).upper() for r in group)
        errors=sum(n for s,n in statuses.items() if s in ('ERROR','FAILED','TIMEOUT'))
        blocked=sum(n for s,n in statuses.items() if any(k in s for k in ('BLOCK','NEEDS_USER','INVALID','NOT_READY')))
        completed=sum(n for s,n in statuses.items() if s in ('COMPLETED','SUCCESS','OK','COMPONENT_RETURNED','VALIDATED','EXECUTED'))
        latency=distribution([r.get('latency_ms') for r in group])
        records.append({'method':method,'runs':len(group),'completed_or_returned':completed,
            'error':errors,'blocked':blocked,'other':len(group)-errors-blocked-completed,
            'latency_median_ms':latency['p50'],'latency_iqr_ms':latency['iqr'],
            'latency_measured':latency['measured'],'latency_missing':latency['missing'],
            'raw_status_counts':str(dict(statuses)),
            'scope':'DIAGNOSTIC; different cohorts; not a speed ranking'})
    write_table(root/'figures'/'D1_pilot_operational',records)
    fig,(left,right)=plt.subplots(1,2,figsize=(15,7))
    names=[r['method'] for r in records]
    bottom=[0]*len(records)
    for key,color in [('completed_or_returned','#4888aa'),('error','#c14b40'),('blocked','#d9a52b'),('other','#aaaaaa')]:
        values=[r[key] for r in records]
        left.barh(range(len(records)),values,left=bottom,label=key,color=color)
        bottom=[a+b for a,b in zip(bottom,values)]
    left.set_yticks(range(len(records)),names,fontsize=8)
    left.set_xlabel('Observed rows (component return does not imply task success)')
    left.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.12))
    for i,r in enumerate(records):
        median=r['latency_median_ms']; iqr=r['latency_iqr_ms']
        text='Unmeasured' if median is None else f'{median:.2f} ms; IQR {iqr:.2f} ms'
        if median is not None: right.scatter(median,i,color='#4888aa')
        right.annotate(text,(.02,i),xycoords=('axes fraction','data'),xytext=(0,10),textcoords='offset points',fontsize=8)
    right.set_yticks(range(len(records)),names,fontsize=8)
    right.set_ylim(-.7,max(len(records)-.3,.7)); right.set_xlabel('Observed median latency (ms)')
    fig.suptitle('D1 Operational diagnostic - PILOT\nDifferent component cohorts and environments: no speed-superiority interpretation',fontsize=12)
    fig.tight_layout(rect=(0,0.05,1,.92))
    fig.savefig(root/'figures'/'D1_pilot_operational.png',dpi=150)
    plt.close(fig)


def build_figures(root, tables):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    specs = [
        ('F1_semantic_comparison',1,('semantic_correct','micro_f1'), 'Semantic grounding'),
        ('F2_esr_spatial_evqsr',2,('execution_success','spatial_correct','evqsr'), 'Execution and correctness'),
        ('F3_false_ready_false_block',3,('false_ready_rate','false_block_rate'), 'Validator error rates'),
        ('F4_validator_error_types',3,('TP','FP','FN','TN'), 'Expert-reviewed validator outcomes'),
        ('F5_recovery',4,('recovery_rate','first_repair_success'), 'Recovery'),
        ('F6_ablation',5,('semantic_micro_f1','evqsr'), 'Observed profiles (controlled ablation pending)'),
    ]
    for name, index, metrics, title in specs:
        records = tables[index]
        write_table(root/'figures'/name, records)
        fig, ax = plt.subplots(figsize=(9,5))
        points = []
        for i, row in enumerate(records):
            for j, key in enumerate(metrics):
                value = row.get(key)
                # Confusion count zero is unobserved if no gold predictions exist.
                if index == 3 and not row.get('measured'):
                    value = None
                if value is not None:
                    points.append((i,j,value))
        for j,key in enumerate(metrics):
            selected=[p for p in points if p[1]==j]
            if selected:
                ax.scatter([p[0]+(j-(len(metrics)-1)/2)*.12 for p in selected],
                           [p[2] for p in selected],label=key,s=55)
        if points:
            ax.legend(fontsize=8)
            ax.set_xticks(range(len(records)),[r.get('method',r.get('profile','?')) for r in records],rotation=25)
            ax.set_ylabel('Count' if name.startswith('F4') else 'Rate')
        else:
            ax.text(.5,.5,'NOT_READY\nNo verified expert measurements',ha='center',va='center',transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title+'\nPILOT - NOT FINAL PAPER RESULT')
        fig.tight_layout(); fig.savefig(root/'figures'/(name+'.png'),dpi=150); plt.close(fig)
    name='F7_reliability_latency_tradeoff'
    records=[{'method':r['method'],'latency_ms':r['latency_ms_mean'],
              'evqsr':next((v['evqsr'] for v in tables[2] if v['method']==r['method']),None)} for r in tables[6]]
    write_table(root/'figures'/name,records)
    fig,ax=plt.subplots(figsize=(9,5))
    observed=[r for r in records if r['latency_ms'] is not None and r['evqsr'] is not None]
    for r in observed:
        ax.scatter(r['latency_ms'],r['evqsr']); ax.annotate(r['method'],(r['latency_ms'],r['evqsr']))
    if not observed:
        ax.text(.5,.5,'NOT_READY\nLatency alone cannot establish reliability',ha='center',va='center',transform=ax.transAxes)
    ax.set_xlabel('Measured mean latency (ms)'); ax.set_ylabel('Expert-verified EVQSR')
    ax.set_title('Reliability / latency\nPILOT - NOT FINAL PAPER RESULT')
    fig.tight_layout(); fig.savefig(root/'figures'/(name+'.png'),dpi=150); plt.close(fig)
