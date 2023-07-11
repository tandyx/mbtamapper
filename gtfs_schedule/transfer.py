"""File to hold the Calendar class and its associated methods."""
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, ForeignKey, Column, String
from gtfs_loader.gtfs_base import GTFSBase


class Transfer(GTFSBase):
    """Transfer"""

    __tablename__ = "transfers"

    from_stop_id = Column(
        String,
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    to_stop_id = Column(
        String,
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    transfer_type = Column(String)
    min_transfer_time = Column(Integer)
    min_walk_time = Column(Integer)
    min_wheelchair_time = Column(Integer)
    suggested_buffer_time = Column(Integer)
    wheelchair_transfer = Column(String)
    from_trip_id = Column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    to_trip_id = Column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    index = Column(Integer, primary_key=True, index=False)

    from_stop = relationship(
        "Stop", back_populates="from_stop_transfers", foreign_keys=[from_stop_id]
    )
    to_stop = relationship(
        "Stop", back_populates="to_stop_transfers", foreign_keys=[to_stop_id]
    )
    from_trip = relationship(
        "Trip", back_populates="from_trip_transfers", foreign_keys=[from_trip_id]
    )
    to_trip = relationship(
        "Trip", back_populates="to_trip_transfers", foreign_keys=[to_trip_id]
    )

    to_stop_time = relationship(
        "StopTime",
        primaryjoin="""and_(
            foreign(Transfer.to_trip_id)==StopTime.trip_id,
            foreign(Transfer.to_stop_id)==StopTime.stop_id
            )""",
        viewonly=True,
    )

    from_stop_time = relationship(
        "StopTime",
        primaryjoin="""and_(
            foreign(Transfer.from_trip_id)==StopTime.trip_id,
            foreign(Transfer.from_stop_id)==StopTime.stop_id
            )""",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Transfers(from_stop_id={self.from_stop_id}, to_stop_id={self.to_stop_id})>"

    def as_label(self) -> str:
        """Returns a label for the transfer, in the format of trip_short_name: trip_headsign"""
        return f"{self.to_trip.trip_short_name}: {self.to_stop_time.destination_label}"
