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
        # perform search with provided parameters
        # return results to the user
        return render_template('results.html')
    return 'Invalid request method'

if __name__ == '__main__':
    app.run(debug=True)