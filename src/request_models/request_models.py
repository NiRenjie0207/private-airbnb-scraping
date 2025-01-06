import logging
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirbnbStatusParams(BaseModel):
    username: str
    password: str

    def validate_params(self):
        if not self.username or not self.password:
            logger.error("HTTPException: You need to provide username and password.")
            raise HTTPException(status_code=400, detail="You need to provide username and password.")