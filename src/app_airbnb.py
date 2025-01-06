import sys
import os
import logging

from fastapi import FastAPI, HTTPException
from io import StringIO

from request_models.request_models import AirbnbStatusParams
from utils.get_listing_private_info import fetch_listing_status


app = FastAPI()

log_stream = StringIO()
stream_handler = logging.StreamHandler(log_stream)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger("fastapi")



def get_and_clear_logs():
    logs = log_stream.getvalue()
    log_stream.truncate(0)
    log_stream.seek(0)
    return logs



@app.post("/listing-status-airbnb")
async def listing_status_airbnb(params: AirbnbStatusParams):
    logger.info("Received request for updating listings' status")
    try:
        fetch_listing_status(params.username, params.password)
        logger.info("Listings' status is successfully fetched")
        return {"logs": get_and_clear_logs()}
    except HTTPException as e:
        logger.warning("HTTPException occurred: %s", str(e))
        raise e
    except Exception as e:
        logger.error("Error while fetching listings' status on airbnb: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")