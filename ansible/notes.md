# Notes

If an account last password change is `never`, which could be set via `chage -d -1 <user>`:

  - if max days is set to `19502 <= x <= 19531`, the password expires and prompt for password change
  - if max days is set to `<= 19501`, the password expires and does not prompt for password change
