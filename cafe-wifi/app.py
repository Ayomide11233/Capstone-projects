from flask import Flask, jsonify, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "cafes.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250))
    coffee_price = db.Column(db.String(250))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'map_url': self.map_url,
            'img_url': self.img_url,
            'location': self.location,
            'has_sockets': self.has_sockets,
            'has_toilet': self.has_toilet,
            'has_wifi': self.has_wifi,
            'can_take_calls': self.can_take_calls,
            'seats': self.seats,
            'coffee_price': self.coffee_price,
        }


# Serve the frontend
@app.route('/')
def index():
    return render_template('index.html')


# REST API endpoints
@app.route('/api/cafes', methods=['GET'])
def get_all_cafes():
    location = request.args.get('location')
    has_wifi = request.args.get('has_wifi')
    has_sockets = request.args.get('has_sockets')
    can_take_calls = request.args.get('can_take_calls')

    query = Cafe.query
    if location:
        query = query.filter_by(location=location)
    if has_wifi is not None:
        query = query.filter_by(has_wifi=(has_wifi.lower() == 'true'))
    if has_sockets is not None:
        query = query.filter_by(has_sockets=(has_sockets.lower() == 'true'))
    if can_take_calls is not None:
        query = query.filter_by(can_take_calls=(can_take_calls.lower() == 'true'))

    cafes = query.order_by(Cafe.name).all()
    return jsonify([c.to_dict() for c in cafes])


@app.route('/api/cafes/<int:cafe_id>', methods=['GET'])
def get_cafe(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    return jsonify(cafe.to_dict())


@app.route('/api/cafes', methods=['POST'])
def add_cafe():
    data = request.json
    required = ['name', 'map_url', 'img_url', 'location']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    cafe = Cafe(
        name=data['name'],
        map_url=data['map_url'],
        img_url=data.get('img_url', ''),
        location=data['location'],
        has_sockets=bool(data.get('has_sockets', False)),
        has_toilet=bool(data.get('has_toilet', False)),
        has_wifi=bool(data.get('has_wifi', False)),
        can_take_calls=bool(data.get('can_take_calls', False)),
        seats=data.get('seats', ''),
        coffee_price=data.get('coffee_price', ''),
    )
    db.session.add(cafe)
    db.session.commit()
    return jsonify(cafe.to_dict()), 201


@app.route('/api/cafes/<int:cafe_id>', methods=['PATCH'])
def update_cafe(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    data = request.json
    for field in ['name', 'map_url', 'img_url', 'location', 'seats', 'coffee_price',
                  'has_sockets', 'has_toilet', 'has_wifi', 'can_take_calls']:
        if field in data:
            setattr(cafe, field, data[field])
    db.session.commit()
    return jsonify(cafe.to_dict())


@app.route('/api/cafes/<int:cafe_id>', methods=['DELETE'])
def delete_cafe(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    db.session.delete(cafe)
    db.session.commit()
    return jsonify({'success': f'Cafe {cafe_id} deleted'})


@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = db.session.query(Cafe.location).distinct().order_by(Cafe.location).all()
    return jsonify([l[0] for l in locations])


if __name__ == '__main__':
    app.run(debug=True, port=5001)
