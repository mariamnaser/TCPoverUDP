# Project Break Down

## UDPL
The UDPL function is meant to emulate a TCP connection. This function must:
- [ ] packLoss
- [ ] delay
- [ ] corruption
- [ ] reordering

---
# Inital Approch 

Input -> array* -> array** (Must be size 1024) --> array**.append(-1, #of packets)
