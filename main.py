import os
import tempfile
import base64
import glob
import numpy as np
from flask import Flask, request, redirect, render_template, url_for, send_file
from skimage import io
from skimage.transform import resize
from tensorflow.keras.models import load_model
import uuid  # Agregar esta importación al inicio

# Diccionario para almacenar resultados temporalmente
prediction_cache = {}

# Cargar modelo
model = load_model('model/modelo.h5')
app = Flask(__name__, template_folder="templates/", static_folder="static/")

# Lista de aldeas
aldeas_ninja = ['konoha', 'iwagakure', 'kumogakure', 'kirigakure', 'sunagakure']

# Crear carpetas necesarias si no existen
for folder in aldeas_ninja + ['prediccion']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Página principal para dibujar y predecir
@app.route("/")
def index():
    return render_template("index.html")

# Página para subir dibujos a una aldea específica (para entrenar dataset)
@app.route("/dibujo")
def dibujo():
    return render_template("dibujo.html")

# Subida de imágenes clasificadas (dataset)
@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        aldea = request.form.get('numero')  # El nombre de la carpeta
        if aldea not in aldeas_ninja:
            return "Aldea inválida", 400

        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=aldea) as fh:
            fh.write(base64.b64decode(img_data))
        print("Imagen guardada en", aldea)
    except Exception as err:
        print("Error en upload:", err)
    return redirect("/dibujo", code=302)

# Ruta para preparar el dataset y guardarlo como .npy
@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    etiquetas = []

    for aldea in aldeas_ninja:
        filelist = glob.glob(f'{aldea}/*.png')
        if not filelist:
            continue

        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]  # Canal alfa
        etiquetas_read = np.array([aldea] * images_read.shape[0])

        images.append(images_read)
        etiquetas.append(etiquetas_read)

    images = np.vstack(images)
    etiquetas = np.concatenate(etiquetas)

    np.save('X.npy', images)
    np.save('y.npy', etiquetas)
    return "Dataset preparado correctamente."

# Descargar archivos .npy
@app.route('/X.npy')
def download_X():
    return send_file('./X.npy')

@app.route('/y.npy')
def download_y():
    return send_file('./y.npy')

# Modificar la función predict
@app.route('/predict', methods=['POST'])
def predict():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir='prediccion') as fh:
            fh.write(base64.b64decode(img_data))
            tmp_file_path = fh.name

        imagen = io.imread(tmp_file_path)
        imagen = imagen[:, :, 3]  # canal alfa
        os.remove(tmp_file_path)

        image = imagen / 255.0
        image_resized = resize(image, (28, 28))
        image_resized = image_resized[:, :, np.newaxis]
        image_reshaped = image_resized.reshape(1, *image_resized.shape)

        salida = model.predict(image_reshaped)[0]
        predicciones = salida * 100
        predicciones_formateadas = [f'{p:.2f}' for p in predicciones]
        
        # Generar un ID único para esta predicción
        prediction_id = str(uuid.uuid4())
        
        # Guardar los resultados en cache
        prediction_cache[prediction_id] = {
            'predicciones': predicciones_formateadas,
            'img_data': img_data
        }
        
        # Limpiar cache viejo (opcional, para evitar memoria infinita)
        if len(prediction_cache) > 100:  # Mantener solo las últimas 100 predicciones
            oldest_key = next(iter(prediction_cache))
            del prediction_cache[oldest_key]

        return redirect(url_for('show_predictions', prediction_id=prediction_id))
    except Exception as e:
        print("Error al predecir:", e)
        return redirect("/", code=302)

# Modificar la función show_predictions
@app.route('/predicciones')
def show_predictions():
    prediction_id = request.args.get('prediction_id')
    
    if not prediction_id or prediction_id not in prediction_cache:
        return redirect("/", code=302)
    
    data = prediction_cache[prediction_id]
    nums_lista = [float(x) for x in data['predicciones']]
    img_data = data['img_data']
    
    aldeas = ['Rocas', 'Niebla', 'Hojas', 'Nubes', 'Arena']
    
    # Opcional: limpiar este resultado del cache después de mostrarlo
    # del prediction_cache[prediction_id]
    
    return render_template('Prediccion.html', nums=nums_lista, aldeas=aldeas, img_data=img_data)

if __name__ == "__main__":
    app.run(debug=True)
