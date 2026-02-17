let currentTrackId = null;
let userdataInitial = { custom_title: '', description: '', starred: false, suno: false, hide: false };

function hasUserdataChanges() {
    const form = document.querySelector('.userdata-form');
    if (!form) return false;
    return form.querySelector('#userdata-custom-title').value !== userdataInitial.custom_title
        || form.querySelector('#userdata-description').value !== userdataInitial.description
        || form.querySelector('#userdata-starred').checked !== userdataInitial.starred
        || form.querySelector('#userdata-suno').checked !== userdataInitial.suno
        || form.querySelector('#userdata-hide').checked !== userdataInitial.hide;
}

function updateUnsavedIndicator() {
    const el = document.querySelector('.userdata-unsaved');
    if (el) el.hidden = !hasUserdataChanges();
}

document.querySelector('.userdata-form')?.addEventListener('input', updateUnsavedIndicator);
document.querySelector('.userdata-form')?.addEventListener('change', updateUnsavedIndicator);

window.addEventListener('beforeunload', function(e) {
    if (hasUserdataChanges()) {
        e.preventDefault();
        e.returnValue = '';
    }
});

document.querySelector('.track-list')?.addEventListener('click', function(e) {
    const toggleBtn = e.target.closest('.track-toggle');
    if (toggleBtn) {
        toggleBtn.closest('.track').classList.toggle('expanded');
        return;
    }

    const openBtn = e.target.closest('.track-open');
    if (!openBtn) return;

    if (hasUserdataChanges()) {
        if (!confirm('You have unsaved changes. Discard them?')) return;
    }

    const track = openBtn.closest('.track');
    const path = track.dataset.path;
    const title = track.dataset.title;
    const id = track.dataset.id;
    currentTrackId = id;

    document.querySelector('.main-panel-placeholder').style.display = 'none';
    const detail = document.querySelector('.main-panel-detail');
    detail.style.display = 'flex';

    detail.querySelector('.detail-title').textContent = title;
    detail.querySelector('.detail-id').textContent = id;

    const audio = detail.querySelector('.detail-audio');
    audio.src = '/audio/' + encodeURI(path);
    audio.load();

    document.querySelectorAll('.track').forEach(t => t.classList.remove('active'));
    track.classList.add('active');

    // Load existing userdata for this track
    const form = detail.querySelector('.userdata-form');
    form.querySelector('#userdata-custom-title').value = '';
    form.querySelector('#userdata-description').value = '';
    form.querySelector('#userdata-starred').checked = false;
    form.querySelector('#userdata-suno').checked = false;
    form.querySelector('#userdata-hide').checked = false;
    form.querySelector('.userdata-status').textContent = '';
    form.querySelector('.userdata-unsaved').hidden = true;

    fetch('/track/' + encodeURIComponent(id) + '/userdata')
        .then(r => r.json())
        .then(data => {
            if (currentTrackId !== id) return;
            form.querySelector('#userdata-custom-title').value = data.custom_title || '';
            form.querySelector('#userdata-description').value = data.description || '';
            form.querySelector('#userdata-starred').checked = !!data.starred;
            form.querySelector('#userdata-suno').checked = !!data.suno;
            form.querySelector('#userdata-hide').checked = !!data.hide;
            userdataInitial = {
                custom_title: data.custom_title || '',
                description: data.description || '',
                starred: !!data.starred,
                suno: !!data.suno,
                hide: !!data.hide,
            };
        });
});

document.querySelector('.userdata-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    if (!currentTrackId) return;

    const status = this.querySelector('.userdata-status');
    const formData = new FormData(this);

    fetch('/track/' + encodeURIComponent(currentTrackId) + '/userdata', {
        method: 'POST',
        body: formData,
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            userdataInitial = {
                custom_title: this.querySelector('#userdata-custom-title').value,
                description: this.querySelector('#userdata-description').value,
                starred: this.querySelector('#userdata-starred').checked,
                suno: this.querySelector('#userdata-suno').checked,
                hide: this.querySelector('#userdata-hide').checked,
            };
            updateUnsavedIndicator();
            status.textContent = 'Saved';
            status.className = 'userdata-status success';
            setTimeout(() => { status.textContent = ''; }, 2000);
        }
    })
    .catch(() => {
        status.textContent = 'Error saving';
        status.className = 'userdata-status error';
    });
});
