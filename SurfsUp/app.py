# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import pandas as pd

from flask import Flask, jsonify
import datetime as dt



#################################################
# Database Setup
#################################################
engine = create_engine('sqlite:///Resources/hawaii.sqlite')

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table

measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB'
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes"""
    return (
        f"Available routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

# Returns json output of the last 12 months of precipitation data from all stations.
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Create dictionary to be returned.
    precip_dict = {}

    # Calculate the last 12 months of precipitation data.
    last_date = session.query(measurement.date).all()[-1][0]
    last_date_format = dt.date.fromisoformat(last_date)
    new_date = last_date_format - dt.timedelta(days=365)
    new_date_str = new_date.isoformat()
    date_precip = session.query(measurement.date, measurement.prcp) \
                        .filter(measurement.date >= new_date_str)
    
    session.close()
    # Populate dictionary.
    for row in date_precip:
        precip_dict[row['date']] = row['prcp']
    
    return jsonify(precip_dict)

# Returns json output of entire weather stations database.
@app.route('/api/v1.0/stations')
def stations():
    station_list = session.query(station.id, 
                                 station.station, 
                                 station.name,
                                 station.latitude,
                                 station.longitude,
                                 station.elevation).all()
    session.close()
    station_data = []

    for row in station_list:
        station_dict = {}
        station_dict["id"] = row.id
        station_dict["station"] = row.station
        station_dict["name"] = row.name
        station_dict["latitude"] = row.latitude
        station_dict["longitude"] = row.longitude
        station_dict["elevation"] = row.elevation
        station_data.append(station_dict)

    return jsonify(station_data)

# Returns json output of temperature values at the most active weather station for the previous year of data.
@app.route('/api/v1.0/tobs')
def temperature():
    # Orders stations by activity.
    station_counts = session.query(measurement.station,
                               func.count(measurement.station)) \
                               .group_by(measurement.station) \
                               .order_by(func.count(measurement.station).desc())
    
    # Retrieves name of the most active station.
    most_active = station_counts[0][0]

    # Finds date of last 12 months of data.
    last_date = session.query(measurement.date).all()[-1][0]
    last_date_format = dt.date.fromisoformat(last_date)
    new_date = last_date_format - dt.timedelta(days=365)
    new_date_str = new_date.isoformat()

    temp_data = session.query(measurement.date, measurement.tobs) \
            .filter(measurement.station == most_active) \
            .filter(measurement.date >= new_date_str).all()
    
    session.close()

    temp_dict = {}

    for row in temp_data:
        temp_dict[row.date] = row.tobs

    return jsonify(temp_dict)

# For a given start date, returns the minimum, maximum, and average recorded temperature.
@app.route('/api/v1.0/<start>')
def from_start(start):
    stats = session.query(func.max(measurement.tobs),
                            func.min(measurement.tobs),
                            func.avg(measurement.tobs)) \
                            .filter(measurement.date >= start)
    session.close()

    query_dict = {}
    query_dict["Start Date"] = start
    query_dict["Maximum temperature"] = stats[0][0]
    query_dict["Minimum temperature"] = stats[0][1]
    query_dict["Average temperature"] = stats[0][2]

    return jsonify(query_dict)

# For given start and end dates, returns the minimum, maximum, and average recorded temperature.
@app.route('/api/v1.0/<start>/<end>')
def start_to_end(start, end):
    stats = session.query(func.max(measurement.tobs),
                            func.min(measurement.tobs),
                            func.avg(measurement.tobs)) \
                            .filter(measurement.date >= start) \
                            .filter(measurement.date <= end)
    session.close()

    query_dict = {}
    query_dict["Start Date"] = start
    query_dict["End Date"] = end
    query_dict["Maximum temperature"] = stats[0][0]
    query_dict["Minimum temperature"] = stats[0][1]
    query_dict["Average temperature"] = stats[0][2]

    return jsonify(query_dict)

if __name__ == '__main__':
    app.run(debug=True)
