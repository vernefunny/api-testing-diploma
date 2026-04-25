# Business rules

## Users
- email unique;
- password: 8-64 symbols, at least one digit, at least one special symbol;
- age: 18-120;
- duplicate email -> 409;
- invalid credentials -> 401;
- 5 failed login attempts -> 429.

## Interests
- only existing interest IDs are allowed;
- IDs must be unique;
- max 10 interests.

## Courses
- only published courses can be bought;
- duplicate course purchase -> 409;
- lesson completion requires paid course;
- course rating requires paid course;
- rating range: 1.0-5.0.

## Payments
- payment is created after course purchase;
- installments_count: 2-36;
- installments_term: 1-36.
