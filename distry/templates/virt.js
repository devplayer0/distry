const password = "{{ password }}";

async function heartbeat() {
    await fetch("{{ url_for('vm_heartbeat', id_=id_) }}", {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `password=${password}`
    });
}
async function reset() {
    const res = await fetch("{{ url_for('vm_reset', id_=id_) }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `password=${password}`
    });

    if (res.status >= 400) {
        alert('Failed to hard reset VM');
    }
}
async function launch() {
    const res = await fetch("{{ url_for('vm_launch', id_=id_) }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `password=${password}`
    });

    if (res.status >= 400) {
        alert('Failed to power on VM - is it already running?');
    }
}

window.onload = e => {
    setInterval(heartbeat, {{ heartbeat_interval * 1000 }});

    const novncFrame = document.querySelector('#novnc');
    document.querySelector('#fullscreen').addEventListener('click', e => novncFrame.requestFullscreen());

    document.querySelector('#reset').addEventListener('click', e => {
        if (confirm('Are you sure?')) {
            reset();
        }
    });

    document.querySelector('#launch').addEventListener('click', e => launch());
};
window.onbeforeunload = e => true;
