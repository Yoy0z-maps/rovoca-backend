from rest_framework import routers
from .views import WordView, WordbookView

router = routers.SimpleRouter()
router.register('wordbooks', WordbookView)
router.register('words', WordView)

urlpatterns = router.urls