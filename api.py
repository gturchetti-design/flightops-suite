from flask import Flask, request, jsonify
from flask_cors import CORS
from route import analyze_route, AIRPORTS
from physics import AIRCRAFT

app = Flask(__name__)
CORS(app)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        result = analyze_route(
            origin_code=data['origin'],
            destination_code=data['destination'],
            aircraft_name=data['aircraft'],
            payload_kg=data.get('payload_kg', 15000),
            fuel_price=data.get('fuel_price', 0.75),
            load_factor=data.get('load_factor', 85),
            ticket_price_multiplier=data.get('ticket_multiplier', 1.0),
        )
        result.pop('waypoints', None)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/airports', methods=['GET'])
def airports():
    return jsonify(AIRPORTS)

@app.route('/api/aircraft', methods=['GET'])
def aircraft():
    return jsonify(list(AIRCRAFT.keys()))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    