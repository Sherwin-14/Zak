# Postgresql v/s MongoDB

## Status
Accepted

## Context
The issue was raised to decide between using Postgresql and MongoDB. The discussion focused on the requirement for SQL, which Postgresql supports, whereas MongoDB is a No-SQL database.

## Decision
Implement Postgresql because it is SQL and the use case requires SQL. Do not use MongoDB because it is not SQL.

## Consequences
Postgresql will be used for the project, enabling SQL-based operations. MongoDB will not be used.

## Participants
@Sherwin-14