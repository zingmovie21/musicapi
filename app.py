from fastapi import FastAPI, HTTPException
from ytmusicapi import YTMusic
from typing import Optional
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="YouTube Music Search API")

# Initialize the YTMusic API
ytmusic = YTMusic()

class SearchResponse(BaseModel):
    title: str
    duration: str
    video_id: str
    artists: list[str]
    album: dict
    youtube_music_url: str
    youtube_video_url: str
    song_thumbnail_url: str
    album_thumbnail_url: Optional[str]

@app.get("/search/", response_model=list[SearchResponse])
async def search_songs(query: str, filter_type: str = 'songs', limit: int = 5):
    """
    Search for songs on YouTube Music and return enriched metadata
    
    Args:
        query: Search query string
        filter_type: Type of search filter (default: songs)
        limit: Maximum number of results to return (default: 5)
    """
    try:
        search_results = ytmusic.search(query, filter=filter_type, limit=limit)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No results found")
        
        enriched_results = []
        
        for song in search_results:
            video_id = song.get('videoId', 'N/A')
            
            # Handle multiple artists
            artists = song.get('artists', [])
            artist_names = [artist['name'] for artist in artists] if artists else ['N/A']
            
            # Get album details
            album = song.get('album', {})
            album_id = album.get('id', None)
            
            # Construct album data
            album_data = {
                'name': album.get('name', 'N/A'),
                'id': album_id,
                'url': f"https://music.youtube.com/browse/{album_id}" if album_id else "N/A"
            }
            
            # Get album thumbnail if available
            album_thumbnail_url = None
            if album_id:
                try:
                    album_details = ytmusic.get_album(album_id)
                    album_thumbnail_url = album_details.get('thumbnails', [{}])[-1].get('url', None)
                except Exception:
                    pass
            
            # Construct URLs
            youtube_music_url = f"https://music.youtube.com/watch?v={video_id}" if video_id != 'N/A' else 'N/A'
            youtube_video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id != 'N/A' else 'N/A'
            
            # Get song thumbnail URL (highest resolution)
            song_thumbnail_url = song.get('thumbnails', [{}])[-1].get('url', 'N/A')
            
            result = SearchResponse(
                title=song.get('title', 'N/A'),
                duration=song.get('duration', 'N/A'),
                video_id=video_id,
                artists=artist_names,
                album=album_data,
                youtube_music_url=youtube_music_url,
                youtube_video_url=youtube_video_url,
                song_thumbnail_url=song_thumbnail_url,
                album_thumbnail_url=album_thumbnail_url
            )
            
            enriched_results.append(result)
        
        return enriched_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint that provides API information"""
    return {
        "name": "YouTube Music Search API",
        "version": "1.0",
        "description": "API for searching songs on YouTube Music with enriched metadata",
        "endpoints": {
            "search": "/search/?query=<search_term>&filter_type=songs&limit=5"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
