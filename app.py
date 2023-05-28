from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('search.html')


@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        departure_date = request.form['departure_date']
        return_date = request.form['return_date']
        nonstop = request.form.get('nonstop')
        airlines = request.form.getlist('airlines')

        transit_cities = []
        transit_times = []

        transit_city_1 = request.form.get('transit_city_1')
        transit_time_1 = request.form.get('transit_time_1')
        transit_cities.append(transit_city_1)
        transit_times.append(transit_time_1)

        transit_city_2 = request.form.get('transit_city_2')
        transit_time_2 = request.form.get('transit_time_2')
        transit_cities.append(transit_city_2)
        transit_times.append(transit_time_2)

        # Продолжайте добавлять transit_city_N и transit_time_N для каждого дополнительного поля

        # Выполните поиск с указанными параметрами
        # Верните результаты пользователю
        return render_template('results.html')

    return 'Invalid request method'


if __name__ == '__main__':
    app.run(debug=True)