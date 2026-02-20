/* === Track list filtering === */
function applyFilters() {
    const starred = document.getElementById('filter-starred')?.checked;
    const title = (document.getElementById('filter-title')?.value || '').toLowerCase();
    const desc = (document.getElementById('filter-desc')?.value || '').toLowerCase();

    const tracks = document.querySelectorAll('.track-list .track');
    let visible = 0;
    tracks.forEach(t => {
        let show = true;
        if (starred && t.dataset.starred !== '1') show = false;
        if (title && !t.dataset.title.toLowerCase().includes(title)) show = false;
        if (desc) {
            const inDesc = (t.dataset.description || '').toLowerCase().includes(desc);
            const inCap = (t.dataset.caption || '').toLowerCase().includes(desc);
            if (!inDesc && !inCap) show = false;
        }
        t.classList.toggle('filter-out', !show);
        if (show) visible++;
    });

    const countEl = document.querySelector('.track-count');
    if (countEl) {
        const anyActive = starred || title || desc;
        countEl.textContent = anyActive
            ? visible + ' / ' + tracks.length + ' tracks'
            : tracks.length + ' tracks';
    }
}

document.getElementById('filter-starred')?.addEventListener('change', applyFilters);
document.getElementById('filter-title')?.addEventListener('input', applyFilters);
document.getElementById('filter-desc')?.addEventListener('input', applyFilters);

/* === Track thumbnails in sidebar === */
function setTrackThumb(trackEl, imgUrl) {
    const thumb = trackEl.querySelector('.track-thumb');
    if (thumb) {
        thumb.style.backgroundImage = 'url(' + imgUrl + ')';
        thumb.style.backgroundSize = 'cover';
    }
}

document.querySelectorAll('.track-list .track').forEach(t => {
    const id = t.dataset.id;
    if (!id) return;
    const imgUrl = '/music_image/' + encodeURIComponent(id) + '.png';
    fetch(imgUrl, { method: 'HEAD' }).then(r => {
        if (r.ok) setTrackThumb(t, imgUrl);
    });
});

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

    const thumbContainer = detail.querySelector('.detail-thumb-container');
    thumbContainer.innerHTML = '';
    const imgUrl = '/music_image/' + encodeURIComponent(id) + '.png';
    fetch(imgUrl, { method: 'HEAD' })
        .then(r => {
            if (currentTrackId !== id) return;
            if (r.ok) {
                const img = document.createElement('img');
                img.src = imgUrl;
                img.alt = title;
                thumbContainer.appendChild(img);
            } else {
                const btn = document.createElement('button');
                btn.className = 'btn-generate-image';
                btn.innerHTML = '<span class="btn-generate-icon">🎨</span>Generate image';
                thumbContainer.appendChild(btn);
            }
        })
        .catch(() => {
            if (currentTrackId !== id) return;
            const btn = document.createElement('button');
            btn.className = 'btn-generate-image';
            btn.innerHTML = '<span class="btn-generate-icon">🎨</span>Generate image';
            thumbContainer.appendChild(btn);
        });

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

/* === Generate image button === */
document.querySelector('.detail-thumb-container')?.addEventListener('click', function(e) {
    const btn = e.target.closest('.btn-generate-image');
    if (!btn || btn.disabled) return;

    const id = currentTrackId;
    if (!id) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="generate-spinner"></span>Generating…';

    fetch('/track/' + encodeURIComponent(id) + '/generate_image', { method: 'POST' })
        .then(r => r.json().then(data => ({ status: r.status, data })))
        .then(({ status, data }) => {
            if (currentTrackId !== id) return;
            if (data.ok || status === 409) {
                const freshUrl = '/music_image/' + encodeURIComponent(id) + '.png?t=' + Date.now();
                const img = document.createElement('img');
                img.src = freshUrl;
                img.alt = document.querySelector('.detail-title')?.textContent || '';
                this.innerHTML = '';
                this.appendChild(img);
                const sidebarTrack = document.querySelector('.track[data-id="' + id + '"]');
                if (sidebarTrack) setTrackThumb(sidebarTrack, freshUrl);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-generate-icon">🎨</span>Generate image';
            }
        })
        .catch(() => {
            if (currentTrackId !== id) return;
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-generate-icon">🎨</span>Generate image';
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
