const utils = {
  renameObjectKey(object, oldKey, newKey) {
    Object.defineProperty(object, newKey, Object.getOwnPropertyDescriptor(object, oldKey))
    delete object[oldKey]
    return object
  },
  findSimilarObjectsKeyWithSameValues(object1,object2) {
    const similarKeysWithSameValues = []
    Object.keys(object1).map(key => {
      if (object2.hasOwnProperty(key) && object2[key].val === object1[key].val && key !== 'id') {
        similarKeysWithSameValues.push(key)
      }
      return key
    })
    return similarKeysWithSameValues
  },
  findSimilarObjectsKeyWithDifferentsValues(object1, object2) {
    const similarKeysWithDifferentsValues = []
    Object.keys(object1).map(key => {
      if (object2.hasOwnProperty(key) && object2[key].val !== object1[key].val) {
        similarKeysWithDifferentsValues.push(key)
      }
      return key
    })
    return similarKeysWithDifferentsValues
  },
    getKeyAlreadyDuplicated: (firstEntity, secondEntity) => {
    let keysAlreadyDuplicated = Object.keys(firstEntity).map(key => {
      const keySplitted = key.split('_')
      if (keySplitted.length > 1 && Number(keySplitted[1])) {
        const mappingDuplicateKeyToActualKey = {}
        mappingDuplicateKeyToActualKey[keySplitted[0]] = key
        return mappingDuplicateKeyToActualKey
      }
      else return null
    }).filter(key => key)
    Object.keys(secondEntity).map(keyFromSecondEntity => {
      const keyFromFirstEntity = keysAlreadyDuplicated.filter(key => key[keyFromSecondEntity])
      if (keyFromFirstEntity.length > 0) {
        if (keyFromFirstEntity.filter(
          key =>  firstEntity[key[keyFromSecondEntity]].val === secondEntity[keyFromSecondEntity].val
          ).length === 0) {
            secondEntity = utils.renameObjectKey(
              secondEntity,
              keyFromSecondEntity,
              `${keyFromSecondEntity}_${secondEntity[keyFromSecondEntity].apiSource}`
              )
          }
        else {
          delete secondEntity[keyFromSecondEntity]
        }
      }
      return  keyFromSecondEntity
    })
    return secondEntity
  },
  copyArrayOfArrayWithObject: arrayOfArrayWithObject => {
    const arrayOfArrayCopy =  []
    arrayOfArrayWithObject.map(arrayWithObject => {
      let arrayCopy = []
      arrayWithObject.map(object => {
        arrayCopy.push({ ...object })
      })
      arrayOfArrayCopy.push(arrayCopy)
    })
    return arrayOfArrayCopy
  },
  formatHaystackJson(entities) {
    const entitiesCopy = []
    entities.forEach(entity => {
      const newEntity = {}
      Object.keys(entity).map(function(key, index) {
        newEntity[key] = entity[key].val
      })
      entitiesCopy.push(newEntity)
    })
    return entitiesCopy
  },
  formatValHayson(entityVal) {
    let prefix = entityVal.slice(0, 2)
    let val = entityVal.slice(2)
    if (prefix==='s:') return val
    if (prefix==='m:') return { _kind: 'Marker' }
    if (prefix==='r:') {
      let splittedRef = val.split(' ')
      if (splittedRef.length===1) return { _kind: 'Ref', val: val}
      else return { _kind: 'Ref', val: splittedRef[0], dis: splittedRef.slice(1).join(' ') }
      }
    if (prefix==='n:') {
      let splittedNumber = val.split(' ')
      if (splittedNumber.length===1) return Number(val)
      else return { _kind: 'Num', val: Number(splittedNumber[0]), unit: (splittedNumber.slice(1)).join(' ') }
    }
    if (prefix==='c:') {
      let splittedCoord = val.split(',')
      return { _kind: 'Coord', lat: Number(splittedCoord[0]), lng: Number(splittedCoord[1]) }
    }
    console.log('ERROR', entityVal)
  },
  formatHaystackHayson(entities) {
    const entitiesCopy = []
    entities.forEach(entity => {
      const newEntity = {}
      Object.keys(entity).map(function(key, index) {
        newEntity[key] = utils.formatValHayson(entity[key].val)
      })
      entitiesCopy.push(newEntity)
    })
    return entitiesCopy
  }
}

export default utils
