# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

# Create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

one_year_ago = dt.date(2017, 8, 23) - dt.timedelta(days=365)

#################################################
# Flask Routes
#################################################

# Define homepage route
@app.route("/")
def home():
    return (
        f"Welcome to the Climate App!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

# Define precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    
    # Calculate the date one year from the last date in data set.
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date()
    

    # Perform a query to retrieve the data and precipitation scores
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= func.date(one_year_ago)).\
        order_by(Measurement.date).all()    
    session.close()
                      
    # Convert the query results to a list of dictionaries
    precipitation_list = [{"date": date, "precipitation":prcp} for date, prcp in precipitation_data]
                
    return jsonify(precipitation_list)
                     
# Define the stations route
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    # Query all stations
    station_data = session.query(Station.station, Station.name).all()
                      
    session.close()
                      
    # Convert the query results to a list of dictionaries
    stations_list = [{"station": station, "name": name} for station, name in station_data]
                  
    return jsonify(stations_list)
                      
# Define the tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # Query the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]              
    
    # Query the last 12 months of temperature observation data for the most active station                 
    temperature_data = session.query(Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()
                      
    session.close()                 
    
    # Convert the query results to a list of dictionaries                  
    temperature_list = [{"temperature": temp[0]} for temp in temperature_data]                  
    
    return jsonify(temperature_list)                                       
                      
# Define the start and start/end date route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end=None):
    session = Session(engine)
    
    # Perform a query to retrieve temperature stats
    if end:
        temperature_stats = session.query(func.min(Measurement.tobs),
                                          func.avg(Measurement.tobs),
                                          func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()
    else:
        temperature_stats = session.query(func.min(Measurement.tobs),
                                          func.avg(Measurement.tobs),
                                          func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()
                      
    session.close()            
    
    # Convert the query results to a list of dictionaries
    stats_list = [{"min_temperature": min_temp, "avg_temperature": avg_temp, "max_temperature": max_temp} for min_temp, avg_temp, max_temp in temperature_stats]              
    
    return jsonify(stats_list)                   
                                        
# Run the app
if __name__ == '__main__':
    app.run(debug=True)