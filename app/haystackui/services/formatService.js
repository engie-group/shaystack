/* eslint-disable */
import dataUtils from './dataUtils.js'
import { API_COLORS } from './index.js'
const formatService = {
  formatIdEntity: id => {
    return id.split(' ')[0].substring(2)
  },
  isRef: value => {
    return value.substring(0,2) === 'r:'
  },
  isEntityFromSource: (entitiesFromAllSource, entityId) => {
    let isEntityFromSource = false
    entitiesFromAllSource.map(entities => {
      entities.map(entity => {
        if(entity.id.val === entityId || entity.id.val.split(' ')[0] === entityId.split(' ')[0]) isEntityFromSource = true
      })
    })
    return isEntityFromSource
  },
  formatEntityName: entity => {
    const id = entity.id.val
    const entityName = id.substring(2).split(' ')
    if(entityName.length === 1) {
      if(entity.dis) return entity.dis.val.substring(2)
      return `@${entityName[0]}`
    }
    entityName.shift()
    return entityName.join(' ')
  },
  formatDateRangeUrl(dateRange) {
    if (dateRange.start === 'today' || dateRange.start === 'yesterday') {
      if (dateRange.end === '' || !dateRange.end) return dateRange.start
      else return `${formatService.dateConvertor(dateRange.start).toISOString()},${formatService.dateConvertor(dateRange.end, false).toISOString()}`
    }
    else if (dateRange.end === 'today' || dateRange.end === 'yesterday') {
      if (dateRange.start === '') return dateRange.end
      else return `${formatService.dateConvertor(dateRange.start).toISOString()},${formatService.dateConvertor(dateRange.end).toISOString()}`
    }
    else
      return `${dateRange.start === '' ? '' : formatService.dateConvertor(dateRange.start).toISOString()},${dateRange.end === '' ? '' : formatService.dateConvertor(dateRange.end).toISOString()}`
  },
  dateConvertor(date, isStartDate=true) { // Same Type
    if (date === 'today') return isStartDate ? new Date() : new Date(new Date().setDate(new Date().getDate() + 1))
    else if (date === 'yesterday') return isStartDate ? new Date(new Date().setDate(new Date().getDate() - 1)) : new Date()
    else if (!date) return ''
    else return new Date(date)
  },
  checkDateRangeIsCorrect(dateStart, dateEnd) {
    const dateStartObject = formatService.dateConvertor(dateStart)
    const dateEndObject = formatService.dateConvertor(dateEnd)
    if (dateStartObject === '' || dateEndObject === '') return true
    else return dateStartObject < dateEndObject
  },
  idToNameEntity: entitiesfromAllSource => {
    let mapEntityIdToEntityName = {}
    entitiesfromAllSource.map(entities => {
      entities.map(entity => {
        const entityId = formatService.formatIdEntity(entity.id.val)
        const entityName = formatService.formatEntityName(entity)
        mapEntityIdToEntityName[entityId] = entityName
      })
    })
    return mapEntityIdToEntityName
  },
  formatCharts(historic) {
    return historic.map(point => {
      return [dataUtils.formatDate(point.ts),  dataUtils.formatVal(point.val)]
    })
  },
  formatYAxis: histories => {
    return histories.map(history => dataUtils.formatVal(history.val))
  },
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
  addApiSourceInformationToEntity: (entities, apiNumber) => {
    entities.map(entity => {
      Object.keys(entity).map(key => {
        if (typeof entity[key] === 'string') {
          const newEntityKey = { val: entity[key], apiSource: apiNumber}
          entity[key] = newEntityKey
        }
        else if (typeof entity[key] === 'boolean') {
          const newEntityKey = { val: `b:${entity[key]}`, apiSource: apiNumber}
          entity[key] = newEntityKey
        }
        return entity
      })
    })
    return entities
  },
  addApiSourceInformation: (entitiesFromAllSource) => {
    entitiesFromAllSource.slice().map((entities, index) => {
      entities.map(entity => {
        Object.keys(entity).map(key => {
          if (typeof entity[key] === 'string') {
            const newEntityKey = { val: entity[key], apiSource: index}
            entity[key] = newEntityKey
          }
        })
        return key
      })
      return entity
    })
    return entitiesFromAllSource
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
            secondEntity = formatService.renameObjectKey(
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
  groupAllEntitiesById: entitiesFromAllSources => {
    let entitiesFromAllSourceCopy = formatService.copyArrayOfArrayWithObject(entitiesFromAllSources)
    let initialEntities = entitiesFromAllSourceCopy.shift()
    return entitiesFromAllSourceCopy.reduce((acc, entities) => formatService.groupTwoEntitiesById(acc, entities), initialEntities)
  },
  groupTwoEntitiesById: (entitiesFromFirstSource, entitiesFromSecondSource) => {
    const mergeEntities = []
    entitiesFromFirstSource.map(entityFromFirstSource => {
      const idFromSource = formatService.formatIdEntity(entityFromFirstSource.id.val)
      entitiesFromSecondSource.map(entityFromSecondSource => {  // Refactor complexity
        const idFromSecondSource = formatService.formatIdEntity(entityFromSecondSource.id.val)
        if (idFromSource === idFromSecondSource) {
          const keysWithSameValues = formatService.findSimilarObjectsKeyWithSameValues(
            entityFromFirstSource,
            entityFromSecondSource
          )
          keysWithSameValues.map(key => {
            if(key === 'his') {
              if (typeof entityFromFirstSource[key].apiSource !== 'object') {
                const newApiSourceValue = []
                newApiSourceValue.push(entityFromFirstSource[key].apiSource)
                newApiSourceValue.push(entityFromSecondSource[key].apiSource)
                delete entityFromSecondSource[key]
                entityFromFirstSource[key].apiSource = newApiSourceValue
              }
              else {
                if (!entityFromFirstSource[key].apiSource.find(apiSource => apiSource === entityFromSecondSource[key].apiSource)) {
                  entityFromFirstSource[key].apiSource.push(entityFromSecondSource[key].apiSource)
                  delete entityFromSecondSource[key]
                }
                else delete entityFromSecondSource[key]
              }
            }
            else entityFromSecondSource[key] = entityFromFirstSource[key]
          })
          entityFromSecondSource['id'] = entityFromFirstSource['id']
          entityFromSecondSource = formatService.getKeyAlreadyDuplicated(entityFromFirstSource, entityFromSecondSource)
          const keysWithDifferentValues = formatService.findSimilarObjectsKeyWithDifferentsValues(
            entityFromFirstSource,
            entityFromSecondSource
          )
          keysWithDifferentValues.map(key => {
            if(key === 'id') {
              entityFromSecondSource[key] = entityFromFirstSource[key]
            }
            else {
              entityFromFirstSource = formatService.renameObjectKey(entityFromFirstSource, key, `${key}_${entityFromFirstSource[key].apiSource}`)
              entityFromSecondSource = formatService.renameObjectKey(entityFromSecondSource, key, `${key}_${entityFromSecondSource[key].apiSource}`)
              delete entityFromFirstSource[key]
              delete entityFromSecondSource[key]
            }
          })
          mergeEntities.push({ ...entityFromFirstSource, ...entityFromSecondSource })
          entitiesFromSecondSource = entitiesFromSecondSource.filter(entity => formatService.formatIdEntity(entity.id.val) !== idFromSource)
          entitiesFromFirstSource = entitiesFromFirstSource.filter(entity => formatService.formatIdEntity(entity.id.val) !== idFromSource)
        }
      })
    })
    return mergeEntities.concat(entitiesFromFirstSource.concat(entitiesFromSecondSource))
  },
  getLinkBetweenEntities: (entitiesFromAllSource) => {
    const colors = { fromSource: API_COLORS, outFromSource: '#c1e1ec' }
    const radiusNode = { fromSource: 10, outFromSource: 5 }
    const entitiesLink = []
    const entitiesNameToEntitiesId = formatService.idToNameEntity(entitiesFromAllSource)
    const colorsLinkOutFromSource = []
    entitiesFromAllSource.map(entities => {
      entities.map( entity => {
        const formatedEntityId = entitiesNameToEntitiesId[formatService.formatIdEntity(entity.id.val)]
        Object.keys(entity).map(key => {
          if(typeof entity[key] !== 'boolean') {
            if(formatService.isRef(entity[key].val) && key !== 'id') {
              const formatedEntityIdLinked = entitiesNameToEntitiesId[formatService.formatIdEntity(entity[key].val)] ?
                      entitiesNameToEntitiesId[formatService.formatIdEntity(entity[key].val)] :
                      formatService.formatIdEntity(entity[key].val)
              const formatedLink = [formatedEntityId, formatedEntityIdLinked]
              if(!formatService.isEntityFromSource(entitiesFromAllSource, entity[key].val)) {
                colorsLinkOutFromSource.push({ id: formatedEntityIdLinked, color: colors.outFromSource, marker: { radius: radiusNode.outFromSource } })
              }
              else colorsLinkOutFromSource.push({ id: formatedEntityIdLinked, color: colors.fromSource[entity.id.apiSource - 1], marker: { radius: radiusNode.fromSource } })
              entitiesLink.push(formatedLink)
            }
          }
          return key
        })
        colorsLinkOutFromSource.push({
            id: formatedEntityId, color: colors.fromSource[entity.id.apiSource - 1],
            dis: entity.dis ? entity.dis.val.substring(2) : formatedEntityId, marker: { radius: radiusNode.fromSource }
            }
          )
      })
    })
    return [entitiesLink, colorsLinkOutFromSource, entitiesNameToEntitiesId]
  },
  addApiSourceInEntities(entities, apiHosts) {
    const entitiesCopy = []
    entities.forEach(entity => {
      const newEntity = {}
      Object.keys(entity).map(function(key, index) {
        const apiSource = apiHosts[entity[key].apiSource - 1]
        const val = entity[key].val
        newEntity[key] = { val, apiSource }
      })
      entitiesCopy.push(newEntity)
    })
    return entitiesCopy
  }
}

export default formatService
