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

window.onload = () => {
    setInterval(heartbeat, {{ heartbeat_interval * 1000 }});

    const novncFrame = document.querySelector('#novnc');
    document.querySelector('#fullscreen').addEventListener('click', e => novncFrame.requestFullscreen());
};
