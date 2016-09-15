from __future__ import print_function
import git, sys, datetime, numpy, traceback
from matplotlib import pyplot
import seaborn, progressbar

repo = git.Repo(sys.argv[1])
fm = '%Y'
interval = 7 * 24 * 60 * 60
commit2cohort = {}
commits = []
for commit in repo.iter_commits('master'):
    cohort = datetime.datetime.utcfromtimestamp(commit.committed_date).strftime(fm)
    commit2cohort[commit.hexsha] = cohort
    commits.append(commit)

def get_file_histogram(commit, path):
    h = {}
    try:
        for old_commit, lines in repo.blame(commit, entry.path):
            cohort = commit2cohort[old_commit.hexsha]
            h[cohort] = h.get(cohort, 0) + 1
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()
    return h

last_date = None
curves = {}
ts = []
file_histograms = {}
for commit in reversed(commits):
    if last_date is not None and commit.committed_date < last_date + interval:
        continue
    t = datetime.datetime.utcfromtimestamp(commit.committed_date)
    ts.append(t)
    print(commit.hexsha, t)
    
    last_date = commit.committed_date
    histogram = {}
    entries = [entry for entry in commit.tree.traverse()
               if entry.type == 'blob' and entry.mime_type.startswith('text/')]
    bar = progressbar.ProgressBar(max_value=len(entries))
    for i, entry in enumerate(entries):
        bar.update(i)
        file_histograms[entry.path] = get_file_histogram(commit, entry.path)
        for cohort, count in file_histograms[entry.path].items():
            histogram[cohort] = histogram.get(cohort, 0) + count
            curves.setdefault(cohort, [])

    for cohort, curve in curves.items():
        curve.append(histogram.get(cohort, 0))

    cohorts = list(sorted(curves.keys()))
    y = numpy.array([[0] * (len(ts) - len(curves[cohort])) + curves[cohort] for cohort in cohorts])
    pyplot.clf()
    pyplot.stackplot(ts, y, labels=['Code added in %s' % c for c in cohorts])
    pyplot.legend(loc=2)
    pyplot.ylabel('Lines of code')
    pyplot.savefig('cohorts.png')
        
