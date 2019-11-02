from functools import wraps

from flask import Flask, request, render_template, url_for, redirect, make_response

def js_bool(b):
    return 'true' if b else 'false'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', distros=app.virt.config['distros'])

@app.route('/vms', methods=['POST'])
def new_vm():
    if 'distro' not in request.form:
        return render_template('error.html', message='distro must be provided'), 400
    if request.form['distro'] not in app.virt.config['distros']:
        return render_template('error.html', message=f'Distro {request.form["distro"]} does not exist'), 400

    id_ = app.virt.new_vm(request.form['distro'])
    vm = app.virt.get_vm(id_)
    app.virt.monitor.refresh(id_)

    return redirect(url_for('view_vm', id_=id_, password=vm['vnc']['password']), code=301)

def auth_vm(form=True):
    def decorator(f):
        @wraps(f)
        def wrapped(id_, *args, **kwargs):
            try:
                request.vm = app.virt.get_vm(id_)
            except KeyError:
                return render_template('error.html', message=f'VM with ID {id_} not found'), 404

            params = request.form if form else request.args
            if 'password' not in params:
                return render_template('error.html', message=f'Password required to access VM {id_}'), 401
            if params['password'] != request.vm['vnc']['password']:
                return render_template('error.html', message=f'Incorrect password for VM {id_}'), 403

            return f(id_, *args, **kwargs)
        return wrapped
    return decorator

@app.route('/vms/<id_>')
@auth_vm(form=False)
def view_vm(id_):
    novnc_url = url_for('static', filename='novnc/vnc.html',
        autoconnect=js_bool(True),
        host=request.vm['vnc']['host'],
        port=request.vm['vnc']['port'],
        path=[''],
        encrypt=js_bool(app.virt.config['novnc']['tls']),
        password=request.vm['vnc']['password'])

    return render_template('view-vm.html',
        novnc_url=novnc_url,
        id_=id_,
        password=request.vm['vnc']['password'],
        heartbeat_interval=app.virt.config['heartbeat']['interval'])

@app.route('/vms/<id_>/heartbeat', methods=['PATCH'])
@auth_vm()
def vm_heartbeat(id_):
    app.virt.monitor.refresh(id_)
    return '', 204
