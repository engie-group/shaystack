# URL Provider

Use `HAYSTACK_PROVIDER=shaystack.providers.db` or `HAYSTACK_PROVIDER=shaystack.providers.url`
to use this provider. Add the variable `HAYSTACK_DB=<url>` to expose a Haystack file via the Haystack protocol. The
methods `/read` and `/hisRead` was implemented. The `<url>` may have the classic form (`http://...`, `ftp://...`
, `file://...`, etc.) or can reference an S3 file
(`s3://...` [more...](AWS.md)). The time series to manage history must be referenced in the entity, with the `hisURI`
tag. This URI may be relative and must be in haystack format.

All the file may be zipped. Reference the zipped version with the `.gz` suffix
(eg. `ontology.zinc.gz`)

```console
$ # Demo
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=sample/carytown.zinc \
  shaystack
```

in another shell

```console
$ curl 'http://localhost:3000/haystack/read?filter=site'
air,phone,sensor,occupied,store,damper,enum,temp,tz,tariffHis,sp,area,site,weatherRef,elecCost,hisMode,kwSite,summary,
fan,siteRef,primaryFunction,kind,cmd,geoCountry,elec,lights,geoStreet,occupiedEnd,yearBuilt,siteMeter,geoCoord,
regionRef,occupiedStart,effective,equip,sitePoint,cool,ahu,hvac,costPerHour,unit,lightsGroup,discharge,zone,power,
geoCity,rooftop,navName,outside,point,dis,energy,elecMeterLoad,id,geoAddr,cur,geoState,geoPostalCode,equipRef,meter,
pressure,heat,return,storeNum,his,metro,stage,hisURI
,"804.552.2222",,,✓,,,,"New_York",,,3149.0ft²,✓,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,,,,"Retail Store",,,
"US",,,"3504 W Cary St",20:00:00,1996.0,,"C(37.555385,-77.486903)",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,
,,,,,,,,,,,,"Richmond",,,,,"Carytown",,,@p:demo:r:23a44701-a89a6c66 Carytown,"3504 W Cary St, Richmond, VA",,
"VA","23221",,,,,,1.0,,"Richmond",,
```

To use a *pure URL*, use this sample:

```console
$ # Demo
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=https://shaystack.s3.eu-west-3.amazonaws.com/carytown.zinc \
  shaystack
```

##### Limitations

Because this provider use a local cache with the parsing version of S3 file, it's may be possible to see different
versions if AWS use multiple instances of lambda. To fix that, the environment variable `REFRESH` can be set to delay
the cache refresh (Default value is 15m). Every quarter of an hour, each lambda instance check the list of version for
this file, and refresh the cache in memory, at the same time. If a new version is published just before you start the
lambda, it's may be possible you can't see this new version. You must wait the end of the current quarter, redeploy the
lambda or update the `REFRESH` parameter [more...](AWS.md).
