#ifndef CUSTOM_INT
#define CUSTOM_INT

#define CINT_BITSIZE 8
#define CINT_MAX (~((~0u) << (CINT_BITSIZE-1)))
#define CINT_MIN (1u << (CINT_BITSIZE-1))

typedef struct cint_t{
    int x : CINT_BITSIZE;
} cint_t;

cint_t add(cint_t a, cint_t b);

cint_t sub(cint_t a, cint_t b);

cint_t mul(cint_t a, cint_t b);

#endif