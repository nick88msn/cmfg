# Scattered Manufacturing

Repository for Nicola Mastrandrea's PhD Thesis.

Current Status: Referees Revision.

Contact: Nicola Mastrandrea (@nick88msn, nmastrandrea@unisa.it)

## Related Works
- [Designing a multi-agent system architecture for managing distributed operations within cloud manufacturing](https://link.springer.com/article/10.1007/s12065-020-00390-z)
- [Integrating Capacity and Logistics of Large Additive Manufacturing Networks](https://www.sciencedirect.com/science/article/pii/S2351978920303772)
- [Situation Awareness and Environmental Factors: The EVO Oil Production](https://link.springer.com/chapter/10.1007/978-3-030-00473-6_23)
- [A Queueing Networks-Based Model for Supply Systems](https://link.springer.com/chapter/10.1007/978-3-319-67308-0_38)

## Citation
Please cite using the following BibTex entry:

```
@phdthesis{mastrandrea2020smfg,
    title={Scattered Manufacturing: Developing a Cloud Manufacturing Framework based on autonomous resources},
    author={Mastrandrea, Nicola},
    school={University of Salerno, Itlay},
    year=2021,
    month=05,
    note={arXiv:}
}
```

Download the full compiled thesis from UNISA repo: (still not public).

## Deployment

To deploy this project run

```shell
  pip install -r requirements.txt
```

To run the server

```shell
  python batch_run.py
```
  
## Environment Variables

To run this project, you will need to add the following environment variable to your secrets.py file in the project root directory

```python
MAPBOX_PUBLIC_TOKEN = "YOUR_MAPBOX_API"
```
  
## License

[MIT](https://choosealicense.com/licenses/mit/)
