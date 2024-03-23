---
runme:
  id: 01HSMXWHX9RP5XFPDS0ERZEXKP
  version: v3
---

<table>
  <tr>
    <th>Function</th>
    <th>Inverse Function</th>
  </tr>
  <tr>
    <td>Amount of One at Compound Interest</td>
    <td>Present Value Reversion of One</td>
  </tr>
  <tr>
    <td>$(1+i)^n$</td>
    <td>$(1+i)^{-n}$</td>
  </tr>
  <tr>
    <td>Present Value of an Ordinary Annuity of One</td>
    <td>Installment to Amortize One</td>
  </tr>
  <tr>
    <td>$a(n,i) = \frac{1}{(1+i)^1} + ... + \frac{1}{(1+i)^n} = \frac{1-(1+i)^{-n}}{i}$</td>
    <td>$\frac{i}{1-(1+i)^{-n}}$</td>
  </tr>
  <tr>
    <td>Accumulation of One per Period</td>
    <td>Sinking Fund Factor</td>
  </tr>
  <tr>
    <td>$s(n,i) = (1+i)^{n-1} + ... + (1+i)^1 + 1 = \frac{(1+i)^n - 1}{i}$</td>
    <td>$SFF(n,i) = \frac{1}{s(n,i)} = \frac{i}{(1+i)^n - 1}$</td>
  </tr>
</table>