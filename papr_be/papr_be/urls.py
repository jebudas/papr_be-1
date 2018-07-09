"""papr_be URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from api.api_comments import views_api_comments
from api.api_editions import views_api_editions
from api.api_login import views_api_login
from api.api_metrics import views_api_metrics
from api.api_paprboy import views_api_paprboy
from api.api_search import views_api_search
from api.api_statistics import views_api_statistics
from api.api_user import views_api_user
from api.api_www import views_api_www

urlpatterns = [

    #v1.1
    url(r'^api/atsbtsip1p1/comments/threads/', views_api_comments.ApiCommentThread.as_view()),
    url(r'^api/atsbtsip1p1/comments/replies/', views_api_comments.ApiCommentsReplies.as_view()),
    url(r'^api/atsbtsip1p1/comments/votes/', views_api_comments.ApiCommentsVotes.as_view()),
    url(r'^api/atsbtsip1p1/statistics/chunky/', views_api_statistics.ApiStatistics.as_view()),
    url(r'^api/atsbtsip1p1/statistics/views/', views_api_statistics.ApiStatisticsViews.as_view()),
    url(r'^api/atsbtsip1p1/user/followers/', views_api_user.ApiUserFollowers.as_view()),
    url(r'^api/atsbtsip1p1/user/following/', views_api_user.ApiUserFollowing.as_view()),
    url(r'^api/atsbtsip1p1/user/request_publisher_ability/', views_api_user.ApiRequestPublisherAbility.as_view()),
    url(r'^api/atsbtsip1p1/user/profile/', views_api_user.ApiUser.as_view()),
    url(r'^api/atsbtsip1p1/user/signup/', views_api_user.ApiCreateUser.as_view()),
    url(r'^api/atsbtsip1p1/user/signup_subscriptions/', views_api_user.ApiSignupSubscriptions.as_view()),
    url(r'^api/atsbtsip1p1/user/update_user_subscriptions/', views_api_user.ApiUserSubscribe.as_view()),
    url(r'^api/atsbtsip1p1/user/update/', views_api_user.ApiUpdateUser.as_view()),
    url(r'^api/atsbtsip1p1/share/', views_api_www.ApiShare.as_view()),
    # DEPRECATED . KILL -9 AFTER MAY 2018
    # url(r'^invite/', views_api_user.ApiFormInviteRequest.as_view()),
    # url(r'^api/atsbtsip1p1/www/invite_request/', views_api_user.ApiFormInviteRequest.as_view()),

    #v1.0
    url(r'^admin/', admin.site.urls),
    url(r'^api/hello/', views_api_login.HelloApiView.as_view()),
    url(r'^api/editions/updater', views_api_editions.ApiUpdater),
    url(r'^api/login/authcode/', views_api_login.ApiViewAuthCode.as_view()),
    url(r'^api/metrics/af/', views_api_metrics.ApiMetricsAF.as_view()),
    url(r'^api/notifications/', views_api_comments.ApiNotifications.as_view()),
    url(r'^api/paprboy/deliver/', views_api_paprboy.ApiSubscriptions, name='deliver'),
    url(r'^api/paprboy/gather/', views_api_paprboy.ApiSubscriptions.as_view()),
    url(r'^api/paprboy/edition/', views_api_paprboy.ApiEdition.as_view()),
    url(r'^api/paprboy/publish/', views_api_paprboy.ApiPublish.as_view()),
    url(r'^api/paprboy/archives/', views_api_paprboy.ApiArchives.as_view()),
    url(r'^api/paprboy/saved_posts/', views_api_paprboy.ApiSavedPosts.as_view()),
    url(r'^api/search/featured', views_api_search.ApiGetFeatured.as_view()),
    url(r'^api/search/search', views_api_search.ApiSearch.as_view()),

    #www
    url(r'^$', views_api_www.www_home, name="www_home"),
    url(r'^apple-app-site-association', views_api_www.www_universal_links, name="apple-app-site-association"),
    url(r'^article/$', views_api_www.www_article, name="www_article"),
    # url(r'^s/.+$', views_api_www.ApiShareView.as_view()),
    url(r'^s/.+$', views_api_www.www_share, name="www_share"),

]
