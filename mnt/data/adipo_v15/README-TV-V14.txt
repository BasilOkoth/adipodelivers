AdipoDelivers TV v14 — split-screen premium project broadcast

Replace:
- templates/impact/tv.html
- static/impact/css/tv.css
- static/impact/js/tv-django.js

Main change:
Every project media slide now uses a deliberate 58/42 split:
LEFT = large project photo/video
RIGHT = category, status, title, summary and structured project details

Photo handling:
- wide images use cover
- portrait/narrow images use contain with an ambient background
- no text overlays the project photo
- project details never sit on top of the image

No migration required.
