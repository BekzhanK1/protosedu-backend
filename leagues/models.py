from django.db import models
from django.core.exceptions import ValidationError

from account.models import Child, Student


class League(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rank = models.IntegerField(db_index=True)
    description = models.TextField(null=True, blank=True)
    icon = models.ImageField(upload_to="league_icons/", null=True, blank=True)
    max_players = models.IntegerField(default=30)
    promotions_rate = models.IntegerField()
    demotions_rate = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "League"
        verbose_name_plural = "Leagues"
        ordering = ["rank"]


class LeagueGroup(models.Model):
    league = models.ForeignKey(
        League, related_name="student_groups", on_delete=models.CASCADE
    )
    group_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.league.name} - {self.group_name}"

    class Meta:
        verbose_name = "League Student Group"
        verbose_name_plural = "League Student Groups"
        ordering = ["league", "group_name"]


class LeagueGroupParticipant(models.Model):
    student = models.OneToOneField(
        Student, null=True, blank=True, on_delete=models.CASCADE
    )
    child = models.OneToOneField(Child, null=True, blank=True, on_delete=models.CASCADE)
    league_group = models.ForeignKey(
        LeagueGroup,
        related_name="participants",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    cups_earned = models.IntegerField(default=0, db_index=True)

    @property
    def is_child(self):
        return True if self.child else False

    @property
    def is_student(self):
        return True if self.student else False

    def clean(self):
        """
        Ensure that either `student` or `child` is set, but not both.
        """
        print("Cleaning LeagueGroupParticipant")
        if self.student and self.child:
            raise ValidationError("A participant cannot be both a student and a child.")
        if not self.student and not self.child:
            raise ValidationError("A participant must be either a student or a child.")

    def __str__(self):
        return (
            f"{self.student} - {self.cups_earned}"
            if self.student
            else f"{self.child} - {self.cups_earned}"
        )

    class Meta:
        verbose_name = "League Group Participant"
        verbose_name_plural = "League Group Participants"
        unique_together = ["league_group", "student", "child"]
        ordering = ["-cups_earned"]
