from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import service


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health():
    return {"result": "success"}


@app.post("/analyze_twitter")
async def analyze_twitter(username: str = Form(...)):
    answer, is_failed = await service.analyze_twitter(username)
    if is_failed:
        raise HTTPException(status_code=400, detail="Failed to analyze Twitter account.")
    return {"result": answer}


@app.post("/analyze_youtube")
async def analyze_youtube(url: str = Form(...)):
    load_dotenv('.env')
    answer, is_failed = await service.analyze_youtube(url)
    if is_failed:
        raise HTTPException(status_code=400, detail="Failed to analyze YouTube video.")
    return {"result": answer}


@app.post("/influencer_comparison")
async def influencer_comparison(influencers: list = Form(...)):
    load_dotenv('.env')
    answer, is_failed = await service.compare_influencers(influencers)
    if is_failed:
        raise HTTPException(status_code=400, detail="Failed to analyze influencer comparison.")
    return {"result": answer}


@app.post("/technical_analysis")
async def technical_analysis(influencer_list: list[str]):
    answer = service.technical_analysis(influencer_list)
    return {"result": answer}