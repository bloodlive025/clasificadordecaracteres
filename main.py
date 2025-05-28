import tempfile
import os
from flask import Flask, request, redirect, send_file
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

main_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        
        .bandana-container {
            position: relative;
            display: inline-block;
            margin: 20px auto;
        }
        
        .bandana-background {
            width: 400px;
            height: 200px;
            background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 50%, #a0a0a0 100%);
            border-radius: 20px;
            position: relative;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            border: 3px solid #808080;
        }
        
        /* Remaches de la bandana */
        .remache {
            position: absolute;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle, #ffffff 30%, #c0c0c0 70%);
            border-radius: 50%;
            border: 2px solid #808080;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }
        
            #villageSymbol {
            vertical-align: middle;
            margin-left: 10px;
            width: 50px;
            height: 50px;
    }
        
        .remache-1 { top: 50px; left: 30px; }
        .remache-2 { top: 80px; left: 25px; }
        .remache-3 { top: 110px; left: 30px; }
        .remache-4 { top: 50px; right: 30px; }
        .remache-5 { top: 80px; right: 25px; }
        .remache-6 { top: 110px; right: 30px; }
        
        /* Área de dibujo en el centro */
        .drawing-area {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 150px;
            height: 150px;
            background: rgba(255,255,255,0.1);
            border: 2px dashed rgba(0,0,0,0.3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        #myCanvas {
            border: none;
            border-radius: 50%;
            background: transparent;
        }
        
        .controls {
            text-align: center;
            margin-top: 20px;
        }
        
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 5px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            background: #4CAF50;
            color: white;
        }
        
        button:hover {
            background: #45a049;
        }
        
        .clear-btn {
            background: #f44336;
        }
        
        .clear-btn:hover {
            background: #da190b;
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        
        .instruction {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }
    </style>
</head>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
<script>
var mousePressed = false;
var lastX, lastY;
var ctx;

function getRndInteger(min, max) {
    return Math.floor(Math.random() * (max - min) ) + min;
}

function InitThis() {
    ctx = document.getElementById('myCanvas').getContext("2d");
    
    // Aldeas ninja
    letra = ["konoha", "iwagakure", "kumogakure", "kirigakure", "sunagakure"];
    random = Math.floor(Math.random() * letra.length);
    aleatorio = letra[random];
    const villageImages = {
        konoha: "/static/aldeas/konoha.png",
        iwagakure: "/static/aldeas/iwagakure.png",
        kumogakure: "/static/aldeas/kumogakure.png",
        kirigakure: "/static/aldeas/kirigakure.png",
        sunagakure: "/static/aldeas/sunagakure.png"
    };
    
    document.getElementById('mensaje').innerHTML = 'Dibuja el símbolo de: ' + aleatorio;
    document.getElementById('villageSymbol').src = villageImages[aleatorio];
    document.getElementById('numero').value = aleatorio;
    console.log('Ruta de imagen:', villageImages[aleatorio]);

    $('#myCanvas').mousedown(function (e) {
        mousePressed = true;
        var rect = this.getBoundingClientRect();
        Draw(e.clientX - rect.left, e.clientY - rect.top, false);
    });
    
    $('#myCanvas').mousemove(function (e) {
        if (mousePressed) {
            var rect = this.getBoundingClientRect();
            Draw(e.clientX - rect.left, e.clientY - rect.top, true);
        }
    });
    
    $('#myCanvas').mouseup(function (e) {
        mousePressed = false;
    });
    
    $('#myCanvas').mouseleave(function (e) {
        mousePressed = false;
    });
}

function Draw(x, y, isDown) {
    if (isDown) {
        ctx.beginPath();
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 8;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.closePath();
        ctx.stroke();
    }
    lastX = x; 
    lastY = y;
}

function clearArea() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

function prepareImg() {
    var canvas = document.getElementById('myCanvas');
    document.getElementById('myImage').value = canvas.toDataURL();
}
</script>

<body onload="InitThis();">
    <div align="left">
        <img src="https://upload.wikimedia.org/wikipedia/commons/f/f7/Uni-logo_transparente_granate.png" width="300"/>
    </div>
    
    <h1 id="mensaje">Dibujando...</h1>
    <img id="villageSymbol" style="vertical-align: middle; margin-left: 720px; width: 50px; height: 70px;" src="" alt="Village Symbol">
    <p class="instruction">Dibuja el símbolo de la aldea en el centro de la bandana ninja</p>
    
    <div align="center">
        <div class="bandana-container">
            <div class="bandana-background">
                <!-- Remaches de la bandana -->
                <div class="remache remache-1"></div>
                <div class="remache remache-2"></div>
                <div class="remache remache-3"></div>
                <div class="remache remache-4"></div>
                <div class="remache remache-5"></div>
                <div class="remache remache-6"></div>
                
                <!-- Área de dibujo en el centro -->
                <div class="drawing-area">
                    <canvas id="myCanvas" width="150" height="150"></canvas>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="clear-btn" onclick="javascript:clearArea();return false;">Borrar</button>
        </div>
    </div>
    
    <div align="center">
        <form method="post" action="upload" onsubmit="javascript:prepareImg();" enctype="multipart/form-data">
            <input id="numero" name="numero" type="hidden" value="">
            <input id="myImage" name="myImage" type="hidden" value="">
            <input id="bt_upload" type="submit" value="Enviar">
        </form>
    </div>
</body>
</html>
"""

@app.route("/")
def main():
    return(main_html)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # check if the post request has the file part
        img_data = request.form.get('myImage').replace("data:image/png;base64,","")
        aleatorio = request.form.get('numero')
        print(aleatorio)
        with tempfile.NamedTemporaryFile(delete = False, mode = "w+b", suffix='.png', dir=str(aleatorio)) as fh:
            fh.write(base64.b64decode(img_data))
        #file = request.files['myImage']
        print("Image uploaded")
    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)


@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    aldeasNinja = ["konoha", "iwagakure", "kumogakure", "kirigakure", "sunagakure"]
    aldeas = []
    for aldea in aldeasNinja:
      filelist = glob.glob('{}/*.png'.format(aldea)) # Busca Patrones
      images_read = io.concatenate_images(io.imread_collection(filelist))#Las imagenes que se encuentran en file list son guardadas como un tipo
      # imageCollection usando io.imread_collection
      #concatenate_images convierte la coleccion en un solo arreglo numpy de tres dimensiones en este caso,(a,x,y) donde a representa a que imagen
      #pertenece, x la posicion que se encuentra el pixel en el eje x y "y"  donde se encuentra el pixel en el eje y
      images_read = images_read[:, :, :, 3]#Extrae el canal de las imagenes, este es el canal de transparencia
      aldeas_read = np.array([aldea] * images_read.shape[0])#Escribe en aldeas_read el nombre de la aldea
      # varias veces. En este caso escribe el nombre un numero igual a las imagenes leidas
      images.append(images_read)
      aldeas.append(aldeas_read)
    images = np.vstack(images)#Concatena las imagenes en un solo arreglo numpy
    aldeas = np.concatenate(aldeas)#Concatena los nombres de las aldeas
    np.save('X.npy', images)
    np.save('y.npy', aldeas)
    return "OK!"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file('./X.npy')
@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file('./y.npy')


if __name__ == "__main__":
    # Crea directorios para cada vocal rusa
    aldeas_ninja = ['konoha', 'iwagakure', 'kumogakure', 'kirigakure', 'sunagakure']
    for aldea in aldeas_ninja:
        if not os.path.exists(str(aldea)):
            os.mkdir(str(aldea))
    app.run()