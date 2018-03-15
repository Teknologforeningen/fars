from django.db import models

class Bookable(models.Model):
    name = models.TextField()
    description = models.TextField()

class Timeslot(models.Model):
    start = models.TimeField()
    end = models.TimeField()
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)

class Booking(models.Model):
    name = models.TextField(default="Booking")
    date = models.DateField()
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    class Meta:
        unique_together= ["name", "date", "timeslot"]
