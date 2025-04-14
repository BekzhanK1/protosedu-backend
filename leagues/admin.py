from django.contrib import admin
from .models import League, LeagueGroup, LeagueGroupParticipant
from django.utils.translation import gettext_lazy as _


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "rank", "max_players", "promotions_rate", "demotions_rate")
    search_fields = ("name",)
    list_filter = ("rank",)
    ordering = ("rank",)
    fieldsets = (
        (None, {"fields": ("name", "rank")}),
        (_("League Details"), {"fields": ("description", "icon")}),
        (
            _("League Settings"),
            {"fields": ("max_players", "promotions_rate", "demotions_rate")},
        ),
    )


@admin.register(LeagueGroup)
class LeagueGroupAdmin(admin.ModelAdmin):
    list_display = ("league", "group_name", "created_at")
    search_fields = ("group_name",)
    list_filter = ("league",)
    ordering = ("league", "group_name")
    fieldsets = (
        (None, {"fields": ("league", "group_name")}),
        (_("Group Details"), {"fields": ("created_at",)}),
    )


@admin.register(LeagueGroupParticipant)
class LeagueGroupParticipantAdmin(admin.ModelAdmin):
    list_display = ("student", "child", "league_group", "cups_earned")
    search_fields = ("student__name", "child__name")
    list_filter = ("league_group",)
    ordering = ("league_group", "cups_earned")
    fieldsets = (
        (None, {"fields": ("student", "child")}),
        (_("League Group"), {"fields": ("league_group",)}),
        (_("Cups Earned"), {"fields": ("cups_earned",)}),
    )
