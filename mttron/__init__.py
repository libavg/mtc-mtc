import os
from libavg.AVGAppUtil import getMediaDir, createImagePreviewNode
from . import mttron

__all__ = [ 'apps', ]

def createPreviewNode(maxSize):
    filename = os.path.join(getMediaDir(__file__), 'preview.png')
    return createImagePreviewNode(maxSize, absHref = filename)

apps = (
        {'class': mttron.MtTron,
            'createPreviewNode': createPreviewNode},
        )
