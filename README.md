# Scattered Manufacturing

Repository for Nicola Mastrandrea's PhD Thesis.

Current Status: Referees Revision.

Contact: Nicola Mastrandrea (@nick88msn, nmastrandrea@unisa.it)

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
